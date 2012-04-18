#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pkg_resources
import gettext
import base64
import re
import logging
from StringIO import StringIO
from PIL import Image
from lxml import etree
from zope.interface import implements
from clacks.common.handler import IInterfaceHandler
from clacks.common import Environment
from clacks.common.utils import parseURL, makeAuthURL
from clacks.common.components.registry import PluginRegistry
from clacks.common.components.amqp import EventConsumer
from clacks.common.components import AMQPServiceProxy

# Set locale domain
t = gettext.translation('messages', pkg_resources.resource_filename("amires", "locale"),
        fallback=False)
_ = t.ugettext


class AsteriskNotificationReceiver(object):
    implements(IInterfaceHandler)
    _priority_ = 99

    TYPE_MAP = {'CallMissed': _("Missed call"),
                'CallEnded': _("Call ended"),
                'IncomingCall': _("Incoming call")}

    resolver = {}
    renderer = {}

    def __init__(self):
        self.env = env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.debug("initializing asterisk number resolver")

        self.__default_image = Image.open(pkg_resources.resource_filename("amires", "data/phone.png"))

        # Load resolver
        for entry in pkg_resources.iter_entry_points("phone.resolver"):
            module = entry.load()
            self.log.debug("loading resolver module '%s'" % module.__name__)
            obj = module()
            self.resolver[module.__name__] = {
                    'object': obj,
                    'priority': obj.priority,
            }

        # Load renderer
        for entry in pkg_resources.iter_entry_points("notification.renderer"):
            module = entry.load()
            self.log.debug("loading renderer module '%s'" % module.__name__)
            self.renderer[module.__name__] = {
                    'object': module(),
                    'priority': module.priority,
            }

        self.last_event = None

    def serve(self):
        self.log.info("listening for asterisk events...")
        amqp = PluginRegistry.getInstance('AMQPHandler')
        EventConsumer(self.env,
            amqp.getConnection(),
            xquery="""
                declare namespace f='http://www.gonicus.de/Events';
                let $e := ./f:Event/f:AMINotification
                return $e/f:Call
            """,
            callback=self.process)

        self.__cr = PluginRegistry.getInstance("CommandRegistry")

    # Event callback
    def process(self, data):
        dat = data.AMINotification['Call']

        # Load information into dict
        event = {}
        for t in dat.iterchildren():
            tag = re.sub(r"^\{.*\}(.*)$", r"\1", t.tag)
            if t.tag == 'From':
                event[tag] = t.text.split(" ")[0]
            else:
                event[tag] = str(t.text)

        # Simple debouncing
        if self.last_event['From'] == event['From'] and self.last_event['To'] == event['To'] and self.last_event['Type'] == event['Type'] and (float(event['Timestamp']) - float(self.last_event['Timestamp'])) < 1:
               return

        self.last_event = event

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

        # Fallback to original number if nothing has been found
        if not i_from:
            i_from = {'contact_phone': event['From'], 'contact_name': event['From'],
                    'company_name': None, 'resource': 'none'}
        if not i_to:
            i_to = {'contact_phone': event['To'], 'contact_name': event['To'],
                    'company_name': None, 'resource': 'none'}

        # Render messages
        to_msg = from_msg = ""
        for mod, info in sorted(self.renderer.iteritems(),
                key=lambda k: k[1]['priority']):

            if 'ldap_uid' in i_to and i_to['ldap_uid']:
                to_msg += info['object'].getHTML(i_from, event)
                to_msg += "\n\n"

            if 'ldap_uid' in i_from and i_from['ldap_uid'] and event['Type'] == 'CallEnded':
                from_msg += info['object'].getHTML(i_to, event)
                from_msg += "\n\n"

        # encode as ASCII with hexadecimal HTML entities for non-latin1 chars
        to_msg = to_msg.encode('ascii', 'xmlcharrefreplace')
        from_msg = from_msg.encode('ascii', 'xmlcharrefreplace')

        # Define avatar view
        if 'avatar' in i_from and i_from['avatar']:
            f_img = Image.open(StringIO(i_from['avatar']))
        else:
            f_img = self.__default_image
        if 'avatar' in i_to and i_to['avatar']:
            t_img = Image.open(StringIO(i_to['avatar']))
        else:
            t_img = self.__default_image

        # Scale image to a reasonable size and convert it to base64
        mw = int(self.env.config.get("amires.avatar_size", default="96"))
        sx, sy = f_img.size
        if sx >= sy:
            f_img.thumbnail((mw, int(sy * mw / sx)))
        else:
            f_img.thumbnail((int(sx * mw / sy), mw))
        sx, sy = t_img.size
        if sx >= sy:
            t_img.thumbnail((mw, int(sy * mw / sx)))
        else:
            t_img.thumbnail((int(sx * mw / sy), mw))

        out = StringIO()
        f_img.save(out, format="PNG")
        out.seek(0)
        f_image_data = "base64:" + base64.b64encode(out.read())

        out = StringIO()
        t_img.save(out, format="PNG")
        out.seek(0)
        t_image_data = "base64:" + base64.b64encode(out.read())

        # Send from/to messages as needed
        amqp = PluginRegistry.getInstance('AMQPHandler')
        if from_msg:
            self.__cr.call("notifyUser", i_from['ldap_uid'],
            self.TYPE_MAP[event['Type']], from_msg.strip(), timeout=10, level='normal', icon=t_image_data)

        if to_msg:
            self.__cr.call("notifyUser", i_to['ldap_uid'],
            self.TYPE_MAP[event['Type']], to_msg.strip(), timeout=10, level='normal', icon=f_image_data)
