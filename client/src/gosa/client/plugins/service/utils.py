# -*- coding: utf-8 -*-
import dbus
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

    def __init__(self):
        env = Environment.getInstance()
        self.env = env

    @Command()
    def setRunlevel(self, runlevel):
        """
        This method forwards the call the clacks-dbus
        """
        #TODO comment
        bus = dbus.SystemBus()
        gosa_dbus = bus.get_object('com.gonicus.gosa', '/com/gonicus/gosa/service')
        result = gosa_dbus.set_runlevel(runlevel, dbus_interface="com.gonicus.gosa")
        print "Result:", result
        return result

