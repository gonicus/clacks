# -*- coding: utf-8 -*-
import dbus
import os
import logging
from dbus.exceptions import DBusException
from lxml import etree
from zope.interface import implements
from clacks.common.handler import IInterfaceHandler
from clacks.common.components import Plugin, PluginRegistry
from clacks.common.components import Command
from _dbus_bindings import INTROSPECTABLE_IFACE


class DBusProxyException(Exception):
    pass


class DBUSProxy(Plugin):
    """
    DBus service plugin.

    This plugin is a proxy for dbus-methods registered by the
    clacks-dbus.

    Each method that is registered for service 'org.clacks'
    can be accessed by calling callDBusMethod, except for
    anonymous methods (those starting with _ or :)
    """
    implements(IInterfaceHandler)
    _target_ = 'service'
    _priority_ = 5

    log = None
    bus = None
    clacks_dbus = None
    methods = None

    # Type map for signature checking
    _type_map = {
                 'i': [int],
                 'n': [int],
                 'x': [int],
                 'q': [int],
                 'y': [chr],
                 'u': [int],
                 't': [int],
                 'b': [bool],
                 's': [unicode, str],
                 'o': [object],
                 'd': [float]}

    def __init__(self):
        self.log = logging.getLogger(__name__)

        # The service we are using
        service = "org.clacks"

        # Get a dbus proxy and check if theres a service registered called 'org.clacks'
        # if not, then we can skip all further processing. (The clacks-dbus seems not to be running)
        self.bus = dbus.SystemBus()
        self.methods = {}
        if not service in self.bus.list_names():
            self.log.debug("no dbus service registered for '%s'. The clacks-dbus seems not to be running!" % (service))
        else:
            try:
                self.log.debug('loading dbus-methods registered by clacks (introspection)')
                self.methods = self._call_introspection(service, "/")
                self.log.debug("found %s registered dbus methods" % (str(len(self.methods))))
            except DBusException as exception:
                self.log.debug("failed to load dbus methods (e.g. check rights in dbus config): %s" % (str(exception)))

    def _call_introspection(self, service, path, methods = None):
        """
        Introspects the dbus service with the given service and path.

        =============== ================
        key             description
        =============== ================
        service         The dbus service we want to introspect. (e.g. org.clacks)
        path            The path we want to start introspection from. (e.g. '/' or '/org/clacks')
        methods         A dictionary used internaly to build up a result.
        =============== ================

        This method returns a dictionary containing all found methods
        with their path, service and parameters.
        """

        # Start the 'Introspection' method on the dbus.
        data = self.bus.call_blocking(service, path, INTROSPECTABLE_IFACE,
                'Introspect', '', (), utf8_strings=True)

        # Return parsed results.
        if methods == None:
            methods = {}
        return self._introspection_handler(data, service, path, methods)

    def _introspection_handler(self, data, service, path, methods):
        """
        Parses the result of the dbus method 'Introspect'.

        It will recursivly load information for newly received paths and methods,
        by calling '_call_introspection'.

        =============== ================
        key             description
        =============== ================
        data            The result of the dbus method call 'Introspect'
        service         The dbus service that was introspected
        path            The path we introspected
        methods         A dictionary used internaly to build up a result.
        =============== ================
        """

        # Transform received XML data into a python object.
        res = etree.fromstring(data)

        # Check for a xml-node containing dbus-method information.
        #
        # It looks like this:
        #       <node name="/org/clacks/notify">
        #         <interface name="org.clacks">
        #           <method name="notify_all">
        #             <arg direction="in"  type="s" name="title" />
        #             ...
        #           </method>
        #         </interface>
        #       ...
        #       </node>
        if res.tag == "node" and res.get('name'):

            # Get the path name this method is registered to (e.g. /org/clacks/notify)
            path = res.get('name')

            # add all found methods to the list of known ones
            for entry in res:
                if entry.tag == "interface" and entry.get("name") == service:
                    for method in entry.iterchildren():

                        # Skip method names that start with _ or : (anonymous methods)
                        m_name = method.get('name')
                        if m_name.startswith('_') or m_name.startswith(':'):
                            continue

                        # Check if this method name is already registered.
                        if m_name in methods:
                            raise DBusProxyException("Duplicate dbus method found '%s'! See (%s, %s)" % (
                                m_name, path, methods[m_name]['path']))

                        # Append the new method to the list og known once.
                        methods[m_name] = {}
                        methods[m_name]['path'] = path
                        methods[m_name]['service'] = service
                        methods[m_name]['args'] = {}

                        # Extract method parameters
                        for arg in method.iterchildren():
                            if arg.tag == "arg" and arg.get("direction") == "in":
                                methods[m_name]['args'][arg.get('name')] = arg.get('type')

        # Check for a xml-node which introduces new paths
        #
        # It will look like this:
        #       <node>
        #         <node name="inventory"/>
        #         <node name="notify"/>
        #         <node name="service"/>
        #         <node name="wol"/>
        #       </node>
        #
        # Request information about registered services by calling 'Introspect' for each path again
        else:
            for entry in res:
                if entry.tag == "node":
                    sname = entry.get('name')
                    self._call_introspection(service, os.path.join(path, sname), methods)
        return methods

    def serve(self):
        """
        This method registeres all known methods to the command registry.
        """
        ccr = PluginRegistry.getInstance('ClientCommandRegistry')
        for name in self.methods.keys():
            ccr.register('system_' + name, 'DBUSProxy.callDBusMethod', [name], ['(signatur)'], 'docstring')

    @Command()
    def listDBusMethods(self):
        """ This method lists all callable dbus methods """
        return self.methods

    @Command()
    def callDBusMethod(self, method, *args):
        """ This method allows to access registered dbus methods by forwarding methods calls """

        """
        ======= ==============
        Key     Description
        ======= ==============
        method  The name of the method to call on dbus side.
        ...     A list of parameters for the method call.
        ======= ==============
        """

        # Check given method and parameters
        self._check_parameters(method, args)

        # Now call the dbus method with the given list of paramters
        mdata = self.methods[method]
        cdbus = self.bus.get_object(mdata['service'], mdata['path'])
        method = cdbus.get_dbus_method(method, dbus_interface=mdata['service'])
        returnval = method(*args)
        return returnval

    def _check_parameters(self, method, args):
        """
        Checks if the given list of arguments (args) are compatible with the
        given dbus-method (method)

        ======= ==============
        Key     Description
        ======= ==============
        method  The name of the method.
        args    The list of arguments to check for.
        ======= ==============
        """

        # Check if the requested dbus method is registered.
        if method not in self.methods:
            raise NotImplementedError(method)

        # Get list of required argument
        m_args = self.methods[method]['args']
        given = ""
        args = list(args)

        # Check each argument
        cnt = 0
        for argument in m_args:
            cnt += 1

            # Does the argument exists
            try:
                given = args.pop(0)
            except IndexError:
                raise TypeError("the parameter '%s' is missing" % argument)

            # Check if the given argument matches the required signature type
            found = True
            if m_args[argument] in self._type_map:
                found = False
                for p_type in self._type_map[m_args[argument]]:
                    if isinstance(given, p_type):
                        found = True

            if not found:
                types = ", ".join(map(lambda x: x.__name__, self._type_map[m_args[argument]]))
                raise TypeError("the parameter %s (%s) is of invalid type. Expected: %s" % (argument, str(cnt), types))

        # We received more arguments than required by the dbus method...
        if len(args):
            raise TypeError("%s() takes exactly %s arguments (%s given)" % (method, len(m_args), cnt+len(args)))

