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

import platform
import logging
from threading import Thread
from qpid.messaging import Connection, ConnectionError, Message, uuid4
from qpid.messaging.util import auto_fetch_reconnect_urls
from qpid.messaging.exceptions import NotFound, SessionClosed, SessionError
from qpid.util import connect, ssl
from qpid.connection import Connection as DirectConnection
from lxml import etree, objectify

from clacks.common.utils import parseURL, makeAuthURL
from clacks.common import Environment
from clacks.common.components.registry import PluginRegistry

# Import pythoncom for win32com / threads
if platform.system() == "Windows":
    #pylint: disable=F0401
    import pythoncom #@UnresolvedImport


class AMQPHandler(object):
    """
    This class handles the AMQP connection, incoming and outgoing connections.
    """
    _conn = None
    __capabilities = {}
    __peers = {}
    _eventProvider = None

    def __init__(self):
        env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.debug("initializing AMQP handler")
        self.env = env
        self.config = env.config

        # Initialize parser
        schema_root = etree.XML(PluginRegistry.getEventSchema())
        schema = etree.XMLSchema(schema_root)
        self._parser = objectify.makeparser(schema=schema)

        # Evaluate username
        user = self.env.uuid
        password = self.config.get("amqp.key")

        # Load configuration
        self.url = parseURL(makeAuthURL(self.config.get('amqp.url'), user, password))
        self.reconnect = self.config.get('amqp.reconnect', True)
        self.reconnect_interval = self.config.get('amqp.reconnect_interval', 3)
        self.reconnect_limit = self.config.get('amqp.reconnect_limit', 0)

        # Go for it
        self.start()

    def __del__(self):
        self.log.debug("shutting down AMQP handler")
        self._conn.close()

    def start(self):
        """
        Enable AMQP queueing. This method puts up the event processor and
        sets it to "active".
        """
        self.log.debug("enabling AMQP queueing")

        # Evaluate username
        user = self.env.uuid
        password = self.config.get("amqp.key")

        # Create initial broker connection
        url = "%s:%s" % (self.url['host'], self.url['port'])
        self._conn = Connection.establish(url, reconnect=self.reconnect,
            username=user,
            password=password,
            transport=self.url['transport'],
            reconnect_interval=self.reconnect_interval,
            reconnect_limit=self.reconnect_limit)

        # Do automatic broker failover if requested
        if self.config.get('amqp.failover', False):
            auto_fetch_reconnect_urls(self._conn)

        # Create event exchange
        socket = connect(self.url['host'], self.url['port'])
        if self.url['scheme'][-1] == 's':
            socket = ssl(socket)
        user = self.env.uuid
        connection = DirectConnection(sock=socket,
                username=user,
                password=self.config.get("amqp.key"))
        connection.start()
        session = connection.session(str(uuid4()))
        # pylint: disable=E1103
        session.exchange_declare(exchange=self.env.domain, type="xml")
        connection.close()

        # Create event provider
        self._eventProvider = EventProvider(self.env, self.getConnection())

    def getConnection(self):
        """
        Returns an AMQP connection handle for further usage.

        ``Return:`` :class:`qpid.messaging.Connection`
        """
        return self._conn

    def checkAuth(self, user, password):
        """
        This function checks a username / password combination using
        the AMQP service' SASL configuration.

        =============== ============
        Parameter       Description
        =============== ============
        user            Username
        password        Password
        =============== ============

        ``Return:`` Bool, success or failure
        """
        # Strip username/password parts of url
        url = "%s:%s" % (self.url['host'], self.url['port'])

        # Don't allow blank authentication
        if user == "" or password == "":
            return False

        try:
            conn = Connection.establish(url, transport=self.url['transport'], username=user, password=password)
            conn.close()
        except ConnectionError as e:
            self.log.debug("AMQP service authentication reports: %s" % str(e))
            return False
        except Exception as e:
            self.log.critical("cannot proceed with authentication")
            self.log.exception(e)
            return False

        return True

    def sendEvent(self, data, user=None):
        """
        Send and validate an event thru AMQP service.

        =============== ============
        Parameter       Description
        =============== ============
        data            XML string or etree object representing the event.
        =============== ============

        ``Return:`` Bool, success or failure
        """
        try:
            event = u"<?xml version='1.0'?>\n"
            if isinstance(data, basestring):
                event += data
            else:
                event += etree.tostring(data, pretty_print=True)

            # Validate event
            if hasattr(self, '_parser'):
                xml = objectify.fromstring(event, self._parser)
            else:
                #TODO: retrieve schema from server
                xml = objectify.fromstring(event)

            # If a user was supplied, check if she's authorized...
            if user:
                acl = PluginRegistry.getInstance("ACLResolver")
                topic = ".".join([self.env.domain, 'event', xml.__dict__.keys()[0]])
                if not acl.check(user, topic, "x"):
                    raise EventNotAuthorized("sending the event '%s' is not permitted" % topic)

            return self._eventProvider.send(event)

        except etree.XMLSyntaxError as e:
            if not isinstance(data, basestring):
                data = data.content
            if self.env:
                self.log.error("event rejected (%s): %s" % (str(e), data))
            raise


class AMQPWorker(object):
    """
    AMQP worker container. This object creates a number of worker threads
    for the defined sender and receiver addresses. It registers receiver
    callbacks for incoming packets.

    =============== ============
    Parameter       Description
    =============== ============
    env             :class:`clacks.common.env.Environment` object
    connection      :class:`qpid.messaging.Connection` object
    s_address       address used to create a sender instance
    r_address       address used to create a receiver instance
    workers         number of worker threads
    callback        method to be called on incoming messages
    =============== ============

    """
    sender = None
    receiver = None
    callback = None

    def __init__(self, env, connection, s_address=None, r_address=None, workers=0, callback=None):
        self.env = env
        self.log = logging.getLogger(__name__)

        self.callback = callback

        # Get reader handle
        self.__ssn = connection.session()
        if s_address:
            self.log.debug("creating AMQP sender for %s" % s_address)
            self.sender = self.__ssn.sender(s_address, capacity=100)

        # Get one receiver object or...
        if not r_address or workers == 0:
            self.receiver = None

        # ... start receive workers
        else:
            for i in range(workers):
                self.log.debug("creating AMQP receiver (%d) for %s" % (i, r_address))
                self.__ssn.receiver(r_address, capacity=100)
                proc = AMQPProcessor(self.__ssn, self.callback)
                proc.start()
                self.env.threads.append(proc)

    def close(self):
        self.__ssn.close(timeout=5)


class AMQPProcessor(Thread):
    """
    AMQP worker thread. This objects get instantiated by the AMQPWorker
    class. It is responsible for receiving the messages and calling the
    callback function.

    =============== ============
    Parameter       Description
    =============== ============
    ssn             AMQP session
    callback        method to be called when receiving AMQP messages
    =============== ============
    """
    __callback = None
    __ssn = None

    def __init__(self, ssn, callback):
        Thread.__init__(self)
        self.setDaemon(True)
        self.__ssn = ssn
        self.__callback = callback
        self.env = Environment.getInstance()

    def run(self):
        # Co-initialize COM for windows
        if platform.system() == "Windows":
            pythoncom.CoInitialize()

        try:
            while True:
                msg = self.__ssn.next_receiver().fetch()
                self.invokeCallback(msg)
        except NotFound as e:
            self.env.log.critical("AMQP main loop stopped: %s" % str(e))
            self.env.requestRestart()
        except SessionClosed as e:
            self.env.log.warning("AMQP session has gone away")
        except SessionError as e:
            self.env.log.error("AMQP error: %s" % str(e))

    def invokeCallback(self, msg):
        return self.__callback(self.__ssn, msg)

    def stop(self):
        self.__ssn.close()


class EventNotAuthorized(Exception):
    pass


class EventProvider(object):

    def __init__(self, env, conn):
        self.env = env
        self.log = logging.getLogger(__name__)

        # Prepare session and sender
        self.__sess = conn.session()
        self.__user = conn.username
        self.__sender = self.__sess.sender("%s/event" % env.domain)

    def send(self, data):
        self.log.debug("sending event: %s" % data)
        msg = Message(data)
        msg.user_id = self.__user
        try:
            return self.__sender.send(msg)
        except NotFound as e:
            self.log.critical("cannot send event: %s" % str(e))
            self.env.requestRestart()
            return False


class EventConsumer(object):

    def __init__(self, env, conn, xquery=".", callback=None):
        self.env = env
        self.log = logging.getLogger(__name__)

        # Assemble subscription query
        queue = 'event-listener-%s' % uuid4()
        address = """%s; {
            create: always,
            delete:always,
            node: {
                durable: False,
                x-declare: {
                    exclusive: True,
                    auto-delete: True }
            },
            link: {
                x-bindings: [
                        {
                            exchange: '%s',
                            queue: %s,
                            key: event,
                            arguments: { xquery: %r}
                        }
                    ]
                }
            }""" % (queue, self.env.domain, queue, xquery)

        # Get session and create worker
        self.__sess = conn.session()

        # Add processor for core.event queue
        self.__callback = callback
        self.__eventWorker = AMQPWorker(self.env, connection=conn,
                        r_address=address,
                        workers=1,
                        callback=self.__eventProcessor)

    def close(self):
        self.__eventWorker.close()

    #pylint: disable=W0613
    def __eventProcessor(self, ssn, data):

        # Validate event and let it pass if it matches the schema
        try:
            xml = objectify.fromstring(data.content)
            self.log.debug("event received: %s" % data.content)
            self.__callback(xml)
        except etree.XMLSyntaxError as e:
            if self.env:
                self.log.debug("event rejected (%s): %s" % (str(e), data.content))
