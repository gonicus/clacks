# -*- coding: utf-8 -*-
import dbus
import re
import logging
from gosa.common import Environment
from gosa.common.components import Plugin
from gosa.common.components import Command
from gosa.common.components import PluginRegistry, AMQPServiceProxy


class Service(Plugin):
    """
    DBus service plugin.

    This plugin is a proxy for registered dbus-methods.

    Each method that is registered for service 'com.gonicus.gosa'
    with path '/com/gonicus/gosa/service' can be accessed by calling
    callDBusMethod.

    """
    _target_ = 'service'

    log = None
    bus = None
    gosa_dbus = None
    methods = None

    def __init__(self):

        self.log = logging.getLogger(__name__)
        self.bus = dbus.SystemBus()
        self.log.debug('loading dbus-methods registered by clacks (introspection)')
        self.gosa_dbus = self.bus.get_object('com.gonicus.gosa', '/com/gonicus/gosa/service')
        call = self.gosa_dbus._Introspect()
        call.block()

        # Collection methods
        self.methods = {}
        for method in self.gosa_dbus._introspect_method_map:
            if not re.match("^com\.gonicus\.gosa\.", method):
                continue
            name = re.sub("^com\.gonicus\.gosa\.(.*)$", "\\1", method)
            self.methods[name] = self.gosa_dbus._introspect_method_map[method]
        self.log.debug("found %s registered dbus methods" % (len(self.methods)))

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
        m = self.gosa_dbus.get_dbus_method(method, dbus_interface="com.gonicus.gosa")
        returnVal = m(*args)
        return returnVal
