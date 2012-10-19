# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

import pkg_resources
import tornado.websocket
import logging
import re
import os
import hmac
import base64
import time
import rfc822
from datetime import datetime
from clacks.common.gjson import dumps
from hashlib import sha1
from webob import exc, Request, Response #@UnresolvedImport
from zope.interface import implements
from clacks.common.utils import stripNs, N_
from clacks.common.handler import IInterfaceHandler
from clacks.common import Environment
from clacks.common.components import PluginRegistry
from clacks.common.components.amqp import EventConsumer


def extract_cookie(name, secret, data):

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
        self.cache_path = self.env.config.get('gosa.cache_path', default="/cache")
        self.resource_path = pkg_resources.resource_filename('clacks.agent', 'data/templates') #@UndefinedVariable
        self.ws_path = self.env.config.get('gosa.websocket', default="/ws")

        spath = pkg_resources.resource_filename('clacks.agent', 'data/gosa') #@UndefinedVariable
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

        # Register a cache handler
        cache_handler = CacheHandler(self.cache_path)
        self.__http.register(self.cache_path, cache_handler)


class CacheHandler(object):
    http_subtree = True

    def __init__(self, path):
        env = Environment.getInstance()
        self.env = env
        self.__path = path
        self.__secret = env.config.get('http.cookie-secret', default="TecloigJink4")
        self.db = env.get_mongo_db('clacks')

    def __call__(self, environ, start_response):
        req = Request(environ)
        try:
            resp = self.process(req, environ)
        except ValueError, e:
            resp = exc.HTTPBadRequest(str(e))
        except exc.HTTPException, e:
            resp = e
        return resp(environ, start_response)

    def check_cookie(self, environ):
        if "HTTP_COOKIE" in environ:
            info = extract_cookie("ClacksRPC", self.__secret, environ['HTTP_COOKIE'])

            # The cookie seems to be valid - check the session id
            if info:
                jsrpc = PluginRegistry.getInstance("JSONRPCService")
                return jsrpc.check_session(info['REMOTE_SESSION'], info['REMOTE_USER'])

            return False

        return False

    def process(self, req, environ):

        # Check if we're authenticated
        if not self.check_cookie(environ):
            raise exc.HTTPUnauthorized(
                      "Please use the login method to authorize yourself.",
                      allow='POST').exception

        # Strip leading part of the path
        path = environ['PATH_INFO'][len(self.__path):].strip(os.sep)

        # Extract cache entry uuid, attribute, index and subindex
        try:
            uuid, attribute, index, subindex = path.split(os.sep)
        except:
            raise exc.HTTPNotFound().exception

        # Check if we're authorized
        info = extract_cookie("ClacksRPC", self.__secret, environ['HTTP_COOKIE'])

        # Query type and dn from uuid
        tmp = self.db.index.find_one({'_uuid': uuid}, {'dn': 1, '_type': 1})
        if not tmp:
            raise exc.HTTPNotFound().exception

        aclresolver = PluginRegistry.getInstance("ACLResolver")
        topic = "%s.objects.%s.attributes.%s" % (self.env.domain, tmp['_type'], attribute)
        if not aclresolver.check(info['REMOTE_USER'], topic, "r", base=tmp['dn']):
            raise exc.HTTPForbidden().exception

        # Remove extension from subindex
        subindex = os.path.splitext(subindex)[0]

        # Load the cached binary data and serve it
        data = self.db.cache.find_one({'uuid': uuid, 'attribute': attribute,
            subindex: {'$exists': True},
            "%s.%s" % (subindex, index): {'$exists': True}}, {subindex: 1, 'modified': 1})
        if not data:
            raise exc.HTTPNotFound().exception

        # Tell the client that we've no modification?
        lm = req.headers.get('If-Modified-Since')
        if lm:
            lm = rfc822.parsedate(lm)
            if data['modified'] > lm:
                raise exc.HTTPNotModified().exception

        resp = Response(
            content_type='image/jpeg',
            body=str(data[subindex][int(index)]))
        resp.cache_control.max_age = 3600
        resp.cache_control.private = 1
        resp.last_modified = datetime(2007, 1, 1, 12, 0)

        return resp


class Redirector(object):

    def __init__(self, location):
        self.location = location

    def __call__(self, environ, start_response):
        return exc.HTTPFound(location=os.path.join(self.location, "index.html"))(environ, start_response)


class WSHandler(tornado.websocket.WebSocketHandler):

    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger(__name__)
        self.env = Environment.getInstance()
        self.__secret = self.env.config.get('http.cookie-secret', default="TecloigJink4")
        self.__consumer = None

        super(WSHandler, self).__init__(*args, **kwargs)

    def check_cookie(self):
        if "Cookie" in self.request.headers:
            info = extract_cookie("ClacksRPC", self.__secret, self.request.headers['Cookie'])

            # The cookie seems to be valid - check the session id
            if info:
                jsrpc = PluginRegistry.getInstance("JSONRPCService")
                return jsrpc.check_session(info['REMOTE_SESSION'], info['REMOTE_USER'])

            return False

        return False

    def send_message(self, message_type, message):
        self.write_message(dumps([message_type, message]))

    def open(self):
        if not self.check_cookie():
            self.log.warning("access to websocket from %s blocked due to invalid cookie" % self.request.remote_ip)
            return

        # Store user information
        info = extract_cookie("ClacksRPC", self.__secret, self.request.headers['Cookie'])
        self.__user = info['REMOTE_USER']

        self.log.debug("new websocket connection established by %s" % self.request.remote_ip)

        # Add event processor
        amqp = PluginRegistry.getInstance('AMQPHandler')
        self.__consumer = EventConsumer(self.env, amqp.getConnection(),
            xquery="""
                declare namespace f='http://www.gonicus.de/Events';
                let $e := ./f:Event
                return $e/f:Notification
                    or $e/f:ObjectChanged
            """,
            callback=self.__eventProcessor)

        self.send_message("notification", {"title": N_("Server information"), "body": N_("Websockets enabled"), "icon": "dialog-information"})

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

    def _handleObjectChanged(self, data):
        data = data.ObjectChanged

        self.send_message("objectChange", {
            "uuid": data.UUID.text,
            "dn": data.DN.text,
            "lastChanged": data.ModificationTime.text,
            "changeType": data.ChangeType.text,
            })

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
