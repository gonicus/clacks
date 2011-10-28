# -*- coding: utf-8 -*-
import dbus
from gosa.common.components import Plugin
from gosa.common.components import Command
from gosa.common import Environment


class Inventory(Plugin):
    """
    Utility class that contains methods needed to handle WakeOnLAN
    notification functionality.
    """
    _target_ = 'inventory'

    def __init__(self):
        env = Environment.getInstance()
        self.env = env

    @Command()
    def request_inventory(self):

        """ Sent a notification to a given user """

        # Get BUS connection
        bus = dbus.SystemBus()
        gosa_dbus = bus.get_object('com.gonicus.gosa', '/com/gonicus/gosa/inventory')

        # Send notification and keep return code
        result = gosa_dbus.inventory()
        print result

