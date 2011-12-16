# -*- coding: utf-8 -*-
import dbus
import re
from gosa.common import Environment
from gosa.common.components import Plugin
from gosa.common.components import Command
from gosa.common.components import PluginRegistry, AMQPServiceProxy


class Service(Plugin):
    """
    Client service plugin which provides methods to maintain the client
    and all its services.
    """
    _target_ = 'service'
    env = None
    bus = None
    gosa_dbus = None
    methods = None

    def __init__(self):
        env = Environment.getInstance()
        self.env = env
        self.bus = dbus.SystemBus()
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

    def call_dbus_method(self, method, *args):
        """
        This method forwards the call the clacks-dbus
        """

        # Check if requested dbus method is registered.
        if method not in self.methods:
            raise NotImplementedError(method)

        print "Calling", method, args
        return True
