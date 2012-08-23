# -*- coding: utf-8 -*-
import pkg_resources
import tornado.websocket
import logging
import re
import os
import hmac, base64, time
from clacks.common.gjson import dumps
from hashlib import sha1
from webob import exc
from zope.interface import implements
from clacks.common.utils import stripNs, N_
from clacks.common.handler import IInterfaceHandler
from clacks.common import Environment
from clacks.common.components import PluginRegistry, ZeroconfService, JSONRPCException
from clacks.common.components.amqp import EventConsumer


class GOsaService(object):
    implements(IInterfaceHandler)
    _priority_ = 9

    def __init__(self):
        env = Environment.getInstance()
        self.env = env
        self.log = logging.getLogger(__name__)
        self.log.info("initializing GOsa static HTTP and WebSocket service")
        self.path = self.env.config.get('gosa.path', default="/admin")
        self.static_path = self.env.config.get('gosa.static_path', default="/static")
        #pylint: disable=E1101
        self.resource_path = pkg_resources.resource_filename('clacks.agent', 'data/templates')
        self.ws_path = self.env.config.get('gosa.websocket', default="/ws")

        #pylint: disable=E1101
        spath = pkg_resources.resource_filename('clacks.agent', 'data/gosa')
        self.local_path = self.env.config.get('gosa.local', default=spath)

        self.__http = None

    def serve(self):
        # Get http service instance
        self.__http = PluginRegistry.getInstance('HTTPService')

        # Register ourselves
        self.__http.register_static(os.path.join(self.path, "(.*)"), self.local_path)
        self.__http.register_static(os.path.join(self.static_path, "(.*)"), self.resource_path)
        self.__http.register_ws(self.ws_path, WSHandler)

        # Register a redirector for the static handler
        redirector = Redirector(self.path)
        self.__http.register(r"/", redirector)


class Redirector(object):

    def __init__(self, location):
        self.location = location

    def __call__(self, environ, start_response):
        return exc.HTTPFound(location=os.path.join(self.location, "index.html"))(environ, start_response)


class WSHandler(tornado.websocket.WebSocketHandler):

    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger(__name__)
        self.env = Environment.getInstance()
        self.__secret = self.env.config.get('http.cookie_secret', default="TecloigJink4")
        self.__consumer = None

        super(WSHandler, self).__init__(*args, **kwargs)

    def check_cookie(self):
        if "Cookie" in self.request.headers:
            info = self.__extract_cookie("ClacksRPC", self.__secret, self.request.headers['Cookie'])

            # The cookie seems to be valid - check the session id
            if info:
                jsrpc = PluginRegistry.getInstance("JSONRPCService")
                return jsrpc.check_session(info['REMOTE_SESSION'], info['REMOTE_USER'])

            return False

        return False

    def __extract_cookie(self, name, secret, data):

        def make_time(value):
            return time.strftime("%Y%m%d%H%M", time.gmtime(value))

        for item in re.split(r";\s*", data):
            if item.startswith(name + "="):
                cookie = item[len(name):]
                decode = base64.decodestring(cookie.replace("_", "/").replace("~", "="))
                _signature_size = len(hmac.new('x', 'x', sha1).digest())
                _header_size = _signature_size + len(make_time(time.time()))

                signature = decode[:_signature_size]
                expires = decode[_signature_size:_header_size]
                content = decode[_header_size:]

                if signature == hmac.new(secret, content, sha1).digest():
                    if int(expires) > int(make_time(time.time())):
                        res = {}
                        for v in re.split(r";\s*", content):
                            res[v.split("=")[0]] = v.split("=", 1)[1]

                        return res
                    else:
                        # This is the normal case of an expired cookie; just
                        # don't bother doing anything here.
                        return None

                # This case can happen if the server is restarted with a
                # different secret; or if the user's IP address changed
                # due to a proxy.  However, it could also be a break-in
                # attempt -- so should it be reported?
                return None

        return None

    def send_message(self, message_type, message):
        self.write_message(dumps([message_type, message]))

    def open(self):
        if not self.check_cookie():
            self.log.warning("access to websocket from %s blocked due to invalid cookie" % self.request.remote_ip)
            return

        # Store user information
        info = self.__extract_cookie("ClacksRPC", self.__secret, self.request.headers['Cookie'])
        self.__user = info['REMOTE_USER']

        self.log.debug("new websocket connection established by %s" % self.request.remote_ip)

        # Add event processor
        amqp = PluginRegistry.getInstance('AMQPHandler')
        self.__consumer = EventConsumer(self.env, amqp.getConnection(),
            xquery="""
                declare namespace f='http://www.gonicus.de/Events';
                let $e := ./f:Event
                return $e/f:Notification
            """,
            callback=self.__eventProcessor)

        self.send_message("notification", { "title": N_("Server information"), "body": N_("Websockets enabled"), "icon": "dialog-information"})

    def on_message(self, message):
        if not self.check_cookie():
            self.log.warning("access to websocket from %s blocked due to invalid cookie" % self.request.remote_ip)
            return

        self.log.debug("message received on websocket from %s: %s" % (self.request.remote_ip, message))

    def on_close(self):
        # Close eventually existing consumer
        if self.__consumer:
            self.__consumer.close()

        self.__consumer = None

        self.log.debug("closing websocket connection to %s" % self.request.remote_ip)

    def __eventProcessor(self, data):
        eventType = stripNs(data.xpath('/g:Event/*', namespaces={'g': "http://www.gonicus.de/Events"})[0].tag)
        func = getattr(self, "_handle" + eventType)
        func(data)

    def _handleNotification(self, data):
        data = data.Notification

        if data.Target != self.__user:
            return

        title = N_("System notification")
        icon = "dialog-information"
        timeout = 10000
        if hasattr(data, 'Title'):
            title = data.Title.text
        if hasattr(data, 'Icon'):
            icon = data.Icon.text
        if hasattr(data, 'Timeout'):
            timeout = int(data.Timeout.text)

        self.send_message("notification", {
            "title": title,
            "body": data.Body.text,
            "icon": icon, "timeout": timeout})
