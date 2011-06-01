#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pkg_resources
import gettext
import re
from lxml import etree
from gosa.common.env import Environment
from gosa.common.utils import parseURL, makeAuthURL
from gosa.common.components.amqp_proxy import AMQPEventConsumer, \
    AMQPServiceProxy

#TODO: modularize later on, maybe two fetcher: sugar/goforge
from amires.modules.goforge_sect import GOforgeSection, MainSection

# Set locale domain
t = gettext.translation('messages', pkg_resources.resource_filename("amires", "locale"),
        fallback=False)
_ = t.ugettext


class AsteriskNotificationReceiver:
    TYPE_MAP = {'CallMissed': _("Missed call"),
                'CallEnded': _("Call ended"),
                'IncomingCall': _("Incoming call")}

    resolver = {}

    def __init__(self):
        self.env = env = Environment.getInstance()

        # Evaluate AMQP URL
        user = env.config.getOption("id", "amqp", default=None)
        if not user:
            user = env.uuid
        password = env.config.getOption("key", "amqp")
        url = parseURL(makeAuthURL(env.config.getOption('url', 'amqp'), user, password))
        if url['path']:
            self.url = url['source']
        else:
            domain = self.env.config.getOption('domain', 'amqp', default="org.gosa")
            self.url = "/".join([url['source'], domain])

        # Load resolver
        for entry in pkg_resources.iter_entry_points("phone.resolver"):
            module = entry.load()
            self.resolver[module.__name__] = {
                    'object': module(),
                    'priority': module.priority,
            }

        #TODO: make this a dynamically loaded fetcher module
        self.goforge = GOforgeSection()
        self.mainsection = MainSection()

        # Create event consumer
        self.consumer = AMQPEventConsumer(self.url,
            xquery = """
                declare namespace f='http://www.gonicus.de/Events';
                let $e := ./f:Event
                return $e/f:AsteriskNotification
            """,
            callback = self.process)

        self.proxy = AMQPServiceProxy(self.url)

    def __del__(self):
        if hasattr(self, 'consumer') and self.consumer is not None:
            del self.consumer

    def serve(self):
        self.env.log.info("Service running...")
        while True:
            self.consumer.join()

    # Event callback
    def process(self, data):
        # for some reason we need to convert to string and back
        cstr = etree.tostring(data, pretty_print = True)
        dat = etree.fromstring(cstr)

        event = {}
        for t in dat[0]:
            tag = re.sub(r"^\{.*\}(.*)$", r"\1", t.tag)
            if t.tag == 'From':
                event[tag] = t.text.split(" ")[0]
            else:
                event[tag] = str(t.text)

        # Resolve numbers with all resolvers, sorted by priority
        i_from = None
        i_to = None

        for mod, info in sorted(self.resolver.iteritems(),
                key=lambda k: k[1]['priority']):
            if not i_from:
                i_from = info['object'].resolve(event['From'])
            if not i_to:
                i_to = info['object'].resolve(event['To'])
            if i_from and i_to:
                break

        # Back to original numbers
        if not i_from:
            i_from = {'contact_phone': event['From'], 'contact_name': event['From'],
                    'company_name': None}
        if not i_to:
            i_to = {'contact_phone': event['To'], 'contact_name': event['To'],
                    'company_name': None}

        if 'ldap_uid' in i_to and i_to['ldap_uid']:
            # render bubble with BubbleSectionBuilders
            msg = self.mainsection.getHTML(i_from, event)
            msg += self.goforge.getHTML(i_from, event)

            self.proxy.notifyUser(i_to['ldap_uid'], self.TYPE_MAP[event['Type']],
                msg)

        if 'ldap_uid' in i_from and i_from['ldap_uid'] and event['Type'] == 'CallEnded':
            msg = self.mainsection.getHTML(i_from, event)
            msg += self.goforge.getHTML(i_from, event)

            self.proxy.notifyUser(i_from['ldap_uid'], self.TYPE_MAP[event['Type']],
                msg)

def main():
    # For usage inside of __main__ we need a dummy initialization
    # to load the environment, because there's no one who's doing
    # it for us...
    Environment.config = "/etc/gosa/config"
    Environment.noargs = True
    env = Environment.getInstance()

    # Load receiver and serve forever
    handler = AsteriskNotificationReceiver()
    try:
        handler.serve()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
