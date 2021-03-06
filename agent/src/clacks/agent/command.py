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

"""
The *CommandRegistry* is responsible for knowing what kind of commands
are available for users. It works together with the
:class:`clacks.common.components.registry.PluginRegistry` and inspects
all loaded plugins for methods marked with the
:meth:`clacks.common.components.command.Command` decorator. All available
information like *method path*, *command name*, *target queue*,
*documentation* and *signature* are recorded and are available for users
via the :meth:`clacks.agent.command.CommandRegistry.dispatch` method
(or better with the several proxies) and the CLI.

Next to registering commands, the *CommandRegistry* is also responsible
for sending and receiving a couple of important bus events:

================= ==========================
Name              Direction
================= ==========================
NodeCapabilities  send/receive
NodeAnnounce      send/receive
NodeLeave         receive
NodeStatus        receive
================= ==========================

All mentioned signals maintain an internal list of available nodes,
their status and their capabilities - aka collection of supported
methods and their signatures. This information is used to locate a
willing node for methods that the receiving node is not able to
process.

.. note::

    Please take a look at the :ref:`command index <cindex>` for a list
    of valid commands.

-------
"""
import re
import time
import logging
import datetime
import gettext
from pkg_resources import resource_filename #@UnresolvedImport
from threading import Event
from inspect import getargspec, getmembers, ismethod
from zope.interface import implements
from clacks.common.components import PluginRegistry, ObjectRegistry, Command
from clacks.common.handler import IInterfaceHandler
from clacks.common import Environment
from clacks.common.event import EventMaker
from clacks.common.utils import stripNs, N_
from clacks.common.error import ClacksErrorHandler as C
from clacks.common.components import AMQPServiceProxy, Plugin
from clacks.common.components.amqp import EventConsumer
from clacks.agent.exceptions import CommandInvalid, CommandNotAuthorized


# Global command types
NORMAL = 1
FIRSTRESULT = 2
CUMULATIVE = 4


# Register the errors handled  by us
C.register_codes(dict(
    COMMAND_NO_USERNAME=N_("Calling method '%(method)s' without a valid user session is not permitted"),
    COMMAND_NOT_DEFINED=N_("Method '%(method)s' is not defined"),
    PERMISSION_EXEC=N_("No permission to execute method '%(queue)s.%(method)s'"),
    COMMAND_INVALID_QUEUE=N_("Invalid queue '%(queue)s' for method '%(method)s'"),
    COMMAND_TYPE_NOT_DEFINED=N_("No method type '%(type)s' defined"),
    COMMAND_WITHOUT_DOCS=N_("Method '%(method)s' has no documentation")
    ))


class CommandRegistry(Plugin):
    """
    This class covers the registration and invocation of methods
    imported thru plugins.
    """
    implements(IInterfaceHandler)
    _priority_ = 0

    # Target queue
    _target_ = 'core'

    capabilities = {}
    objects = {}
    commands = {}
    nodes = {}
    proxy = {}

    def __init__(self):
        env = Environment.getInstance()
        self.env = env
        self.log = logging.getLogger(__name__)
        self.log.info("initializing command registry")
        self.processing = Event()

    @Command(__help__=N_("Returns the LDAP base"))
    def getBase(self):
        """
        Returns the LDAP base used by the agent as string

        ``Return``: a string representing the LDAP base
        """
        return self.env.base

    @Command(__help__=N_("List available service nodes on the bus."))
    def getNodes(self):
        """
        Returns a list of available nodes.

        ``Return``: list of nodes
        """
        return self.nodes

    @Command(needsQueue=False, __help__=N_("List available methods " +
        "that are registered on the bus."))
    def getMethods(self, queue=None, locale=None):
        """
        Lists the all methods that are available in the domain.

        ================= ==========================
        Parameter         Description
        ================= ==========================
        queue             Ask for methods on special queue, None for all
        locale            Translate __help__ strings to the desired language
        ================= ==========================

        ``Return``: dict describing all methods
        """
        res = {}
        if queue is None:
            queue = self.env.domain + ".command.core"

        if queue == self.env.domain + ".command.core":
            node = None
        else:
            node = queue.split('.')[-1]

        for name, info in self.capabilities.iteritems():

            # Only list local methods
            if node:
                if node in info['provider']:
                    res[name] = info

            # List all available methods where we have
            # non dead providers in the list
            else:
                if self.isAvailable(info['provider']):
                    res[name] = info

            # Adapt to locale if required
            if locale:
                mod = PluginRegistry.getInstance(info['path'].split(".")[0]).get_locale_module()
                t = gettext.translation('messages',
                        resource_filename(mod, "locale"),
                        fallback=True,
                        languages=[locale])
                res[name]['doc'] = t.ugettext(info['doc'])

        return res

    @Command(needsQueue=True, __help__=N_("Shut down the service belonging to the supplied queue. In case of HTTP connections, this command will shut down the node you're currently logged in."))
    def shutdown(self, queue, force=False):
        """
        Shut down the service belonging to the supplied queue. In case of HTTP
        connections, this command will shut down the node you're currently
        logged in.

        ================= ==========================
        Parameter         Description
        ================= ==========================
        force             force global shut down
        ================= ==========================

        ``Return``: True when shutting down
        """
        if not force and queue == self.env.domain + '.command.core':
            return False

        self.log.debug("received shutdown signal - waiting for threads to terminate")
        self.env.active = False
        return True

    def isAvailable(self, providers):
        """
        Check if the list of providers contain at least one
        node which is available.

        ========== ============
        Parameter  Description
        ========== ============
        providers  list of providers
        ========== ============

        ``Return:`` bool flag if at least one available or not
        """
        for provider in providers:
            if provider in self.nodes:
                return True
        return False

    def hasMethod(self, func):
        """
        Check if the desired method is available.

        ========== ============
        Parameter  Description
        ========== ============
        func       method to check for
        ========== ============

        ``Return:`` flag if available or not
        """
        return func in self.commands

    def call(self, func, *arg, **larg):
        """
        *call* can be used to internally call a registered method
        directly. There's no access control happening with this
        method.

        ========== ============
        Parameter  Description
        ========== ============
        func       method to call
        args       ordinary argument list/dict
        ========== ============

        ``Return:`` return value from the method call
        """

        # We pass 'self' as user, to skip acls checks.
        return self.dispatch(self, None, func, *arg, **larg)

    def dispatch(self, user, queue, func, *arg, **larg):
        """
        The dispatch method will try to call the specified function and
        checks for user and queue. Additionally, it carries the call to
        it's really destination (function types, cumulative results) and
        does some sanity checks.

        Handlers like JSONRPC or AMQP should use this function to
        dispatch the real calls.

        ========== ============
        Parameter  Description
        ========== ============
        user       the calling users name
        queue      the queue address where the call originated from
        func       method to call
        args       ordinary argument list/dict
        ========== ============

        Dispatch will...

          * ... forward *unknown* commands to nodes that
            are capable of processing them - ordered by load.

          * ... will take care about the modes *NORMAL*, *FIRSTRESULT*,
            *CUMULATIVE* like defined in the *Command* decorator.

        ``Return:`` the real methods result
        """

        # Check for user authentication (if user is 'self' this is an internal call)
        if not user and user != self:
            raise CommandNotAuthorized(C.make_error("COMMAND_NO_USERNAME", method=func))

        # Check if the command is available
        if not func in self.capabilities:
            raise CommandInvalid(C.make_error("COMMAND_NOT_DEFINED", method=func))

        # Depending on the call method, we may have no queue information
        if not queue:
            queue = self.env.domain + ".command.%s" % self.capabilities[func]['target']

        # Check for permission (if user equals 'self' then this is an internal call)
        if user != self:
            chk_options = dict(dict(zip(self.capabilities[func]['sig'], arg)).items() + larg.items())
            acl = PluginRegistry.getInstance("ACLResolver")
            if not acl.check(user, "%s.%s" % (queue, func), "x", options=chk_options):
                raise CommandNotAuthorized(C.make_error("PERMISSION_EXEC", queue=queue, method=func))

        # Convert to list
        arg = list(arg)

        # Check if the command needs a special queue for being executed,
        # shutdown i.e. may not be very handy if globaly executed.
        if self.callNeedsQueue(func):
            if not self.checkQueue(func, queue):
                raise CommandInvalid(C.make_error("COMMAND_INVALID_QUEUE", queue=queue, method=func))
            else:
                arg.insert(0, queue)

        # Check if call is interested in calling user ID, prepend it
        if self.callNeedsUser(func):
            if user != self:
                arg.insert(0, user)
            else:
                arg.insert(0, None)

        # Handle function type (additive, first match, regular)
        methodType = self.capabilities[func]['type']
        (clazz, method) = self.path2method(self.commands[func]['path'])

        # Type NORMAL, do a straight execute
        if methodType == NORMAL:

            # Do we have this method locally?
            if func in self.commands:
                return PluginRegistry.modules[clazz].\
                        __getattribute__(method)(*arg, **larg)
            else:
                # Sort nodes by load, use first which is in [func][provider]
                provider = None
                nodes = self.get_load_sorted_nodes()

                # Get first match that is a provider for this function
                for provider, node in nodes:
                    if provider in self.capabilities[func]['provider']:
                        break

                # Set target queue directly to the evaulated node which provides that method
                target = self.env.domain + '.command.%s.%s' % (self.capabilities[func]['target'], provider)

                # Load amqp service proxy for that queue if not already present
                if not target in self.proxy:
                    amqp = PluginRegistry.getInstance("AMQPHandler")
                    self.proxy[target] = AMQPServiceProxy(amqp.url['source'], target)

                # Run the query
                methodCall = getattr(self.proxy[target], func)
                return methodCall(*arg, **larg)

        # FIRSTRESULT: try all providers, return on first non exception
        # CUMMULATIVE: try all providers, merge non exception results
        elif methodType == FIRSTRESULT or methodType == CUMULATIVE:
            # Walk thru nodes
            result = None
            for node in self.nodes.keys():

                # Don't bother with non provider nodes, just skip them
                if not node in self.capabilities[func]['provider']:
                    continue

                # Is it me?
                if node == self.env.id:
                    methodCall = PluginRegistry.modules[clazz].__getattribute__(method)
                else:
                    # Set target queue directly to the evaulated node which provides that method
                    target = self.env.domain + '.command.%s.%s' % (self.capabilities[func]['target'], node)

                    # Load amqp service proxy for that queue if not already present
                    if not target in self.proxy:
                        amqp = PluginRegistry.getInstance("AMQPHandler")
                        self.proxy[target] = AMQPServiceProxy(amqp.url['source'], target)

                    methodCall = getattr(self.proxy[target], method)

                # Finally do the call
                try:
                    tmp = methodCall(*arg, **larg)

                    if methodType == FIRSTRESULT:
                        return tmp
                    else:
                        if result is None:
                            result = {}

                        result[node] = tmp

                # We do not care, go to the next..., pylint: disable=W0703
                except Exception:
                    pass

            return result

        else:
            raise CommandInvalid(C.make_error("COMMAND_TYPE_NOT_DEFINED", type=methodType))

    def path2method(self, path):
        """
        Converts the call path (class.method) to the method itself

        ========== ============
        Parameter  Description
        ========== ============
        path       method path including the class
        ========== ============

        ``Return:`` the method name
        """
        return path.rsplit('.')

    def callNeedsUser(self, func):
        """
        Checks if the provided method requires a user parameter.

        ========== ============
        Parameter  Description
        ========== ============
        func       method name
        ========== ============

        ``Return:`` success or failure
        """
        if not func in self.commands:
            raise CommandInvalid(C.make_error("COMMAND_NOT_DEFINED", method=func))

        (clazz, method) = self.path2method(self.commands[func]['path'])

        method = PluginRegistry.modules[clazz].__getattribute__(method)
        return getattr(method, "needsUser", False)

    def callNeedsQueue(self, func):
        """
        Checks if the provided method requires a queue parameter.

        ========== ============
        Parameter  Description
        ========== ============
        func       method name
        ========== ============

        ``Return:`` success or failure
        """
        if not func in self.commands:
            raise CommandInvalid(C.make_error("COMMAND_NOT_DEFINED", method=func))

        (clazz, method) = self.path2method(self.commands[func]['path'])

        method = PluginRegistry.modules[clazz].__getattribute__(method)
        return getattr(method, "needsQueue", False)

    def checkQueue(self, func, queue):
        """
        Checks if the provided method was sent to the correct queue.

        ========== ============
        Parameter  Description
        ========== ============
        func       method name
        queue      queue to compare to
        ========== ============

        ``Return:`` success or failure
        """
        if not func in self.commands:
            raise CommandInvalid(C.make_error("COMMAND_NOT_DEFINED", method=func))

        (clazz, method) = self.path2method(self.commands[func]['path']) #@UnusedVariable
        p = re.compile(r'\.' + self.env.id + '$')
        p.sub('', queue)
        return self.env.domain + '.command.%s' % PluginRegistry.modules[clazz].get_target() == p.sub('', queue)

    def get_load_sorted_nodes(self):
        """
        Return a node list sorted by node *load*.

        ``Return:`` list
        """
        return sorted(self.nodes.items(), lambda x, y: cmp(x[1]['load'], y[1]['load']))

    def __del__(self):
        self.log.debug("shutting down command registry")

    def __eventProcessor(self, data):
        eventType = stripNs(data.xpath('/g:Event/*', namespaces={'g': "http://www.gonicus.de/Events"})[0].tag)
        func = getattr(self, "_handle" + eventType)
        func(data)

    def _handleNodeAnnounce(self, data):
        data = data.NodeAnnounce
        self.log.debug("received hello of node %s" % data.Id)

        # Reply with sending capabilities
        amqp = PluginRegistry.getInstance("AMQPHandler")

        # Send capabilities
        e = EventMaker()
        methods = []
        for command in self.commands:
            info = self.commands[command]
            mtype = {1: 'NORMAL', 2: 'FIRSTRESULT', 3: 'CUMMULATIVE'}[info['type']]
            methods.append(
                e.NodeMethod(
                    e.Name(command),
                    e.Path(info['path']),
                    e.Target(info['target']),
                    e.Signature(','.join(info['sig'])),
                    e.Type(mtype),
                    e.QueueRequired('true' if info['needsQueue'] else 'false'),
                    e.Documentation(info['doc'])))

        for obj, info in ObjectRegistry.objects.iteritems():
            if info['signature']:
                methods.append(
                    e.NodeObject(
                        e.OID(obj),
                        e.Signature(info['signature'])))
            else:
                methods.append(e.NodeObject(e.OID(obj)))

        caps = e.Event(
            e.NodeCapabilities(
                e.Id(self.env.id),
                *methods))

        amqp.sendEvent(caps)

    def _handleNodeCapabilities(self, data):
        data = data.NodeCapabilities
        self.log.debug("received capabilities of node %s" % data.Id)

        # Add methods
        for method in data.NodeMethod:
            methodName = method.Name.text
            if not methodName in self.capabilities:
                mtype = {'NORMAL': 1, 'FIRSTRESULT': 2, 'CUMMULATIVE': 3}
                self.capabilities[methodName] = {
                    'path': method.Path.text,
                    'target': method.Target.text,
                    'sig': method.Signature.text.split(',') if method.Signature.text else [],
                    'type': mtype[method.Type.text],
                    'needsQueue': method.QueueRequired.text == "true",
                    'doc': method.Documentation.text}
                self.capabilities[methodName]['provider'] = []

            # Append the sender as a new provider
            self.capabilities[methodName]['provider'].append(data.Id.text)

        # Add objects
        if hasattr(data, 'NodeObject'):
            for obj in data.NodeObject:
                oid = obj.OID.text
                if not oid in self.objects:
                    self.objects[oid] = []

                # Append the sender as a new provider
                self.objects[oid].append(data.Id.text)

        # We've received at least one capability event, so we're
        # theoretically ready to serve...
        if not self.processing.is_set():
            self.processing.set()

    def _handleNodeStatus(self, data):
        data = data.NodeStatus
        self.log.debug("received status of node %s" % data.Id)

        # Add recieve time to be able to sort out dead nodes
        t = datetime.datetime.utcnow()
        self.nodes[data.Id.text] = {
            'load': float(data.Load),
            'latency': float(data.Latency),
            'workers': int(data.Workers),
            'indexed': bool(data.Indexed),
            'received': time.mktime(t.timetuple())}

    def _handleNodeLeave(self, data):
        """ Receive goodbye messages and act accordingly. """
        data = data.NodeLeave
        sender = data.Id.text
        self.log.debug("received goodbye of node %s" % sender)

        # Remove node from nodes
        if sender in self.nodes:
            del self.nodes[sender]

        # Remove node from capabilites
        capabilities = {}
        for name, info in self.capabilities.iteritems():
            if sender in info['provider']:
                info['provider'].remove(sender)
            if len(info['provider']):
                self.capabilities[name] = info
        self.capabilities = capabilities

    def updateNodes(self):
        """
        Maintain node list. Remove entries that haven't shown up
        in the configured interval.
        """
        nodes = {}
        timeout = self.env.config.get('agent.node-timeout', 60)

        for node, info in self.nodes.iteritems():
            t = datetime.datetime.utcnow()
            if time.mktime(t.timetuple()) - info['received'] < timeout:
                nodes[node] = info

        self.nodes = nodes

    def serve(self):
        """
        Start serving the command registry to the outside world. Send
        hello and register event callbacks.
        """

        # Prepare amqp handler
        amqp = PluginRegistry.getInstance("AMQPHandler")

        for clazz in PluginRegistry.modules.values():
            for mname, method in getmembers(clazz):
                if ismethod(method) and hasattr(method, "isCommand"):
                    func = mname

                    # Adjust documentation
                    if not method.__help__:
                        raise CommandInvalid(C.make_error("COMMAND_WITHOUT_DOCS", method=func))

                    doc = re.sub("(\s|\n)+", " ", method.__help__).strip()

                    self.log.debug("registering %s" % func)
                    info = {
                        'name': func,
                        'path': "%s.%s" % (clazz.__class__.__name__, mname),
                        'target': clazz.get_target(),
                        'sig': [] if not getargspec(method).args else getargspec(method).args,
                        'type': getattr(method, "type", NORMAL),
                        'needsQueue': getattr(method, "needsQueue", False),
                        'doc': doc,
                        }

                    if 'self' in info['sig']:
                        info['sig'].remove('self')

                    self.commands[func] = info

        # Add event processor
        EventConsumer(self.env,
            amqp.getConnection(),
            xquery="""
                declare namespace f='http://www.gonicus.de/Events';
                let $e := ./f:Event
                return $e/f:NodeAnnounce
                    or $e/f:NodeLeave
                    or $e/f:NodeCapabilities
                    or $e/f:NodeStatus
            """,
            callback=self.__eventProcessor)

        # Announce ourselves
        e = EventMaker()
        announce = e.Event(e.NodeAnnounce(e.Id(self.env.id)))
        amqp.sendEvent(announce)

    @Command(needsUser=True, __help__=N_("Return the current session's user ID."))
    def getSessionUser(self, user):
        return user

    @Command(needsUser=True, __help__=N_("Send event to the bus."))
    def sendEvent(self, user, data):
        """
        Sends an event to the AMQP bus. Data must be in XML format,
        see :ref:`Events handling <events>` for details.

        ========== ============
        Parameter  Description
        ========== ============
        data       valid event
        ========== ============

        *sendEvent* will indirectly validate the event against the bundled "XSD".
        """
        amqp = PluginRegistry.getInstance("AMQPHandler")
        amqp.sendEvent(data, user)
