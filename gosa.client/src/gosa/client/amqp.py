# -*- coding: utf-8 -*-
import socket
import thread
import logging
from urlparse import urlparse
from qpid.messaging import Connection
from qpid.messaging.util import auto_fetch_reconnect_urls
from gosa.common.components import AMQPServiceProxy
from gosa.common.components.amqp import AMQPHandler, EventProvider
from gosa.common.components.zeroconf_client import ZeroconfClient
from gosa.common.utils import parseURL
from gosa.common import Environment

# Global lock
a_lock = thread.allocate_lock()


class AMQPClientHandler(AMQPHandler):
    """
    This class handles the AMQP connection, incoming and outgoing connections
    and allows event callback registration.
    """
    _conn = None
    __capabilities = {}
    __peers = {}
    _eventProvider = None
    __proxy = None
    url = None
    joined = False

    def __init__(self):
        """
        Construct a new AMQPClientHandler instance based on the configuration
        stored in the environment.

        @type env: Environment
        @param env: L{Environment} object
        """
        env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.debug("initializing AMQP client handler")
        self.env = env

        # Enable debugging for qpid if we're in debug mode
        #if self.env.config.get('core.loglevel') == 'DEBUG':
        #    enable('qpid', DEBUG)

        # Load configuration
        self.url = parseURL(self.env.config.get('amqp.url', None))
        self.domain = self.env.config.get('ampq.domain', default="org.gosa")
        self.dns_domain = socket.getfqdn().split('.', 1)[1]

        # Use zeroconf if there's no URL
        if not self.url:
            url = ZeroconfClient.discover(['_amqps._tcp', '_amqp._tcp'], domain=self.domain)[0]

            o = urlparse(url)
            # pylint: disable=E1101
            self.domain = o.path[1::]
            self.log.info("using service '%s'" % url)

            # Configure system
            user = self.env.config.get('amqp.id', default=None)
            if not user:
                user = self.env.uuid

            key = self.env.config.get('amqp.key')
            if key:
                # pylint: disable=E1101
                self.url = parseURL('%s://%s:%s@%s' % (o.scheme, user, key, o.netloc))
            else:
                self.url = parseURL(url)

        # Make proxy connection
        self.__proxy = AMQPServiceProxy(self.url['source'])

        # Set params and go for it
        self.reconnect = self.env.config.get('amqp.reconnect', True)
        self.reconnect_interval = self.env.config.get('amqp.reconnect-interval', 3)
        self.reconnect_limit = self.env.config.get('amqp.reconnect-limit', 0)

        # Check if credentials are supplied
        if not self.env.config.get("amqp.key"):
            raise Exception("no key supplied - please join the client")

        # Start connection
        self.start()

    def get_proxy(self):
        return self.__proxy

    def sendEvent(self, data):
        """ Override original sendEvent. Use proxy instead. """
        return self.__proxy.sendEvent(data)

    def start(self):
        """
        Enable AMQP queueing. This method puts up the event processor and
        sets it to "active".
        """
        self.log.debug("enabling AMQP queueing")

        # Evaluate username
        user = self.env.config.get("amqp.id", default=None)
        if not user:
            user = self.env.uuid

        # Create initial broker connection
        url = "%s:%s" % (self.url['host'], self.url['port'])
        self._conn = Connection.establish(url, reconnect=self.reconnect,
            username=user,
            password=self.env.config.get("amqp.key"),
            transport=self.url['transport'],
            reconnect_interval=self.reconnect_interval,
            reconnect_limit=self.reconnect_limit)

        # Do automatic broker failover if requested
        if self.env.config.get('amqp.failover', default=False):
            auto_fetch_reconnect_urls(self._conn)

        # Create event provider
        self._eventProvider = EventProvider(self.env, self._conn)

    def __del__(self):
        self.log.debug("shutting down AMQP client handler")
        self._conn.close()
