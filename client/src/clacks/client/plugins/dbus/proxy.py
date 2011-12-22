# -*- coding: utf-8 -*-
import re
import dbus
import logging
from zope.interface import implements
from clacks.common.handler import IInterfaceHandler
from clacks.common.components import Plugin, PluginRegistry
from clacks.common.components import Command


class DBUSProxy(Plugin):
    """
    DBus service plugin.

    This plugin is a proxy for registered dbus-methods.

    Each method that is registered for service 'org.clacks'
    with path '/org/clacks/service' can be accessed by calling
    callDBusMethod.

    """
    implements(IInterfaceHandler)
    _target_ = 'service'
    _priority_ = 5

    log = None
    bus = None
    gosa_dbus = None
    methods = None

    def __init__(self):
        self.log = logging.getLogger(__name__)

        # Request information about registered dbus methods we can use.
        self.methods = {}

        try:
            self.bus = dbus.SystemBus()
            self.log.debug('loading dbus-methods registered by clacks (introspection)')
            self.gosa_dbus = self.bus.get_object('org.clacks', '/org/clacks/service')
            call = self.gosa_dbus._Introspect()
            call.block()

            # Collection methods
            for method in self.gosa_dbus._introspect_method_map:
                if not re.match("^org\.clacks\.", method):
                    continue

                name = re.sub("^org\.clacks\.(.*)$", "\\1", method)
                self.methods[name] = self.gosa_dbus._introspect_method_map[method]

            self.log.debug("found %s registered dbus methods" % (len(self.methods)))

        except dbus.DBusException as e:
            self.log.debug("failed to load registered dbus methods: %s" % (str(e)))

    def serve(self):
        cr = PluginRegistry.getInstance('ClientCommandRegistry')
        for name in self.methods.keys():
            cr.register('system_' + name, 'DBUSProxy.callDBusMethod', [name], ['(signatur)'], 'docstring')

    @Command()
    def callDBusMethod(self, method, *args):
        """ This method allows to access registered dbus methods by forwarding methods calls """

        """
        ======= ==============
        Key     Description
        ======= ==============
        method  The name of method to call on dbus side.
        ...     A list of parameters for the method call.
        ======= ==============
        """

        # Check if requested dbus method is registered.
        if method not in self.methods:
            raise NotImplementedError(method)

        # Now call the dbus method with the given list of paramters
        method = self.gosa_dbus.get_dbus_method(method,
                dbus_interface="org.clacks")
        returnval = method(*args)
        return returnval
