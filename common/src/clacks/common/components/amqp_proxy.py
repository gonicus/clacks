# -*- coding: utf-8 -*-
from qpid.messaging import Connection, Message, uuid4
from qpid.messaging.util import auto_fetch_reconnect_urls
from types import DictType
from clacks.common.components.json_exception import JSONRPCException
from clacks.common.gjson import dumps, loads
from clacks.common.components.amqp import AMQPProcessor
from clacks.common.utils import parseURL
from lxml import objectify


# Number of AMQP workers for the proxy
WORKERS = 3


class AMQPException(Exception):
    pass


class AMQPServiceProxy(object):
    """
    The AMQPServiceProxy provides a simple way to use clacks RPC
    services from various clients. Using the proxy object, you
    can directly call methods without the need to know where
    it actually gets executed::

        >>> from clacks.common.components import AMQPServiceProxy
        >>> proxy = AMQPServiceProxy('amqp://admin:secret@localhost/org.clacks')
        >>> proxy.getMethods()

    This will return a dictionary describing the available methods.

    =============== ============
    Parameter       Description
    =============== ============
    serviceURL      URL used to connect to the AMQP service broker
    serviceAddress  Address string describing the target queue to bind to, must be skipped if no special queue is needed
    serviceName     *internal*
    conn            *internal*
    worker          *internal*
    methods         *internal*
    =============== ============

    The AMQPService proxy creates a temporary AMQP *reply to* queue, which
    is used for command results.
    """
    worker = {}

    def __init__(self, serviceURL, serviceAddress=None, serviceName=None,
                 conn=None, worker=None, methods=None):
        self.__URL = url = parseURL(serviceURL)
        self.__serviceURL = serviceURL
        self.__serviceName = serviceName
        self.__serviceAddress = serviceAddress
        self.__worker = worker
        self.__domain = url['path']
        self.__methods = methods

        # Prepare AMQP connection if not already there
        if not conn:

            _url = "%s:%s" % (url['host'], url['port'])
            conn = Connection.establish(_url, reconnect=True,
                username=url['user'],
                password=url['password'],
                transport=url['transport'],
                reconnect_interval=3,
                reconnect_limit=0)

            #TODO: configure reconnect
            #auto_fetch_reconnect_urls(conn)

            # Prefill __serviceAddress correctly if domain is given
            if self.__domain:
                self.__serviceAddress = '%s.command.core' % self.__domain

            if not self.__serviceAddress:
                raise AMQPException("no serviceAddress or domain specified")

            if not self.__worker:
                self.__worker = {self.__serviceAddress: {}}

            # Pre instanciate core sessions
            for i in range(0, WORKERS):
                ssn = conn.session(str(uuid4()))
                self.__worker[self.__serviceAddress][i] = {
                        'ssn': ssn,
                        'sender': ssn.sender(self.__serviceAddress),
                        'receiver': ssn.receiver('reply-%s; {create:always, delete:always, node: { type: queue, durable: False, x-declare: { exclusive: False, auto-delete: True } }}' % ssn.name),
                        'locked': False}

        # Store connection
        self.__conn = conn
        self.__ssn = None
        self.__sender = None
        self.__receiver = None
        self.__sess = None

        # Retrieve methods
        if not self.__methods:
            self.__serviceName = "getMethods"
            self.__methods = self.__call__()
            self.__serviceName = None

            # If we've no direct queue, we need to push to different queues
            if self.__domain:
                queues = set([
                        x['target'] for x in self.__methods.itervalues()
                        if x['target'] != 'core'
                    ])

                # Pre instanciate queue sessions
                for queue in queues:
                    for i in range(0, WORKERS):
                        ssn = conn.session(str(uuid4()))
                        self.__worker[queue] = {}
                        self.__worker[queue][i] = {
                                'ssn': ssn,
                                'sender': ssn.sender("%s.command.%s" %
                                    (self.__domain, queue)),
                                'receiver': ssn.receiver('reply-%s; {create:always, delete:always, node: { type: queue, durable: False, x-declare: { exclusive: False, auto-delete: True } }}' % ssn.name),
                                'locked': False}


    def close(self):
        """
        Close the AMQP connection established by the proxy.
        """

        # Close all senders/receivers
        for value in self.__worker.values():
            for vvalue in value.values():
                vvalue['sender'].close()
                vvalue['receiver'].close()

        self.__conn.close()

    #pylint: disable=W0613
    def login(self, user, password):
        return True

    def logout(self):
        return True

    def getProxy(self):
        return AMQPServiceProxy(self.__serviceURL,
                self.__serviceAddress,
                None,
                self.__conn,
                worker=self.__worker,
                methods=self.__methods)

    def __getattr__(self, name):
        if self.__serviceName != None:
            name = "%s.%s" % (self.__serviceName, name)

        return AMQPServiceProxy(self.__serviceURL, self.__serviceAddress, name,
                self.__conn, worker=self.__worker, methods=self.__methods)

    def __call__(self, *args, **kwargs):
        if len(kwargs) > 0 and len(args) > 0:
            raise JSONRPCException("JSON-RPC does not support positional and keyword arguments at the same time")

        # Default to 'core' queue, pylint: disable=W0612
        queue = "core"

        if self.__methods:
            if not self.__serviceName in self.__methods:
                raise NameError("name '%s' not defined" % self.__serviceName)

            if self.__domain:
                queue = self.__methods[self.__serviceName]['target']
            else:
                queue = self.__serviceAddress

        # Find free session for requested queue
        found = False
        for sess, dsc in self.__worker[self.__serviceAddress].iteritems():
            if not dsc['locked']:
                self.__ssn = dsc['ssn']
                self.__sender = dsc['sender']
                self.__receiver = dsc['receiver']
                self.__sess = sess
                dsc['locked'] = True
                found = True
                break

        # No free session?
        if not found:
            raise AMQPException('no free session - increase workers')

        # Send
        if len(kwargs):
            postdata = dumps({"method": self.__serviceName, 'params': kwargs, 'id': 'jsonrpc'})
        else:
            postdata = dumps({"method": self.__serviceName, 'params': args, 'id': 'jsonrpc'})

        message = Message(postdata)
        message.user_id = self.__URL['user']
        message.reply_to = 'reply-%s' % self.__ssn.name

        self.__sender.send(message)

        # Get response
        respdata = self.__receiver.fetch()
        resp = loads(respdata.content)
        self.__ssn.acknowledge(respdata)

        self.__worker[self.__serviceAddress][self.__sess]['locked'] = False

        if resp['error'] != None:
            raise JSONRPCException(resp['error'])

        return resp['result']


class AMQPEventConsumer(object):
    """
    The AMQPEventConsumer can be used to subscribe for events
    and process them thru a callback. The subscription is done
    thru *XQuery*, the callback can be a python method.

    Example listening for an event called *AsteriskNotification*::

        >>> from clacks.common.components import AMQPEventConsumer
        >>> from lxml import etree
        >>>
        >>> # Event callback
        >>> def process(data):
        ...     print(etree.tostring(data, pretty_print=True))
        >>>
        >>> # Create event consumer
        >>> consumer = AMQPEventConsumer("amqps://admin:secret@localhost/org.clacks",
        ...             xquery=\"\"\"
        ...                 declare namespace f='http://www.gonicus.de/Events';
        ...                 let $e := ./f:Event
        ...                 return $e/f:AsteriskNotification
        ...             \"\"\",
        ...             callback=process)

    The consumer will start right away, listening for your events.

    =============== ============
    Parameter       Description
    =============== ============
    url             URL used to connect to the AMQP service broker
    domain          If the domain is not already encoded in the URL, it can be specified here.
    xquery          `XQuery <http://en.wikipedia.org/wiki/XQuery>`_ string to query for events.
    callback        Python method to be called if the event happened.
    =============== ============

    .. note::
       The AMQP URL consists of these parts::

         (amqp|amqps)://user:password@host:port/domain
    """

    def __init__(self, url, domain="org.clacks", xquery=".", callback=None):

        # Build connection
        url = parseURL(url)

        _url = "%s:%s" % (url['host'], url['port'])
        self.__conn = Connection.establish(_url, reconnect=True,
            username=url['user'],
            password=url['password'],
            transport=url['transport'],
            reconnect_interval=3,
            reconnect_limit=0)

        # Do automatic broker failover if requested
        #TODO: configure reconnect
        #auto_fetch_reconnect_urls(self.__conn)

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
            }""" % (queue, domain, queue, xquery)

        # Add processor for core.event queue
        self.__callback = callback
        self.__eventWorker = AMQPStandaloneWorker(
                        self.__conn,
                        r_address=address,
                        workers=1,
                        callback=self.__eventProcessor)

    def __del__(self):
        self.__eventWorker.join()
        self.__conn.close()

    #pylint: disable=W0613
    def __eventProcessor(self, ssn, data):
        # Call callback, let exceptions pass to the caller
        xml = objectify.fromstring(data.content)
        self.__callback(xml)

    def join(self):
        self.__eventWorker.join()


class AMQPStandaloneWorker(object):
    """
    AMQP standalone worker container. This object creates a number of worker threads
    for the defined sender and receiver addresses. It registers receiver
    callbacks for incoming packets.

    =============== ============
    Parameter       Description
    =============== ============
    connection      :class:`qpid.messaging.Connection`
    s_address       Address used to create a sender instance
    r_address       Address used to create a receiver instance
    workers         Number of worker threads
    callback        method to be called on incoming messages
    =============== ============
    """
    sender = None
    receiver = None
    callback = None
    threads = []

    def __init__(self, connection, s_address=None, r_address=None, workers=0, callback=None):
        self.callback = callback

        # Get reader handle
        ssn = connection.session()
        if s_address:
            self.sender = ssn.sender(s_address, capacity=100)

        # Get one receiver object or...
        if not r_address or workers == 0:
            self.receiver = None

        # ... start receive workers
        else:
            #pylint: disable=W0612
            for i in range(workers):
                ssn.receiver(r_address, capacity=100)
                proc = AMQPProcessor(ssn, self.callback)
                proc.start()
                self.threads.append(proc)

    def join(self):
        """
        Join the worker threads.
        """
        for p in self.threads:
            p.join(1)
