# -*- coding: utf-8 -*-
import dbus
from clacks.common.components import Plugin
from clacks.common.components import Command
from clacks.common import Environment


class WakeOnLan(Plugin):
    """
    Utility class that contains methods needed to handle WakeOnLAN
    functionality.
    """
    _target_ = 'wakeonlan'

    def __init__(self):
        env = Environment.getInstance()
        self.env = env

    @Command()
    def wakeonlan(self, macaddr):
        """ Sent a WakeOnLAN paket to the given MAC address. """
        bus = dbus.SystemBus()
        clacks_dbus = bus.get_object('org.clacks',
                                   '/org/clacks/wol')
        return clacks_dbus.wakeOnLan(macaddr, dbus_interface="org.clacks")
