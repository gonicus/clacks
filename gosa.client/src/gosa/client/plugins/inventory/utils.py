# -*- coding: utf-8 -*-
import dbus
from lxml import etree
import StringIO
from gosa.common.event import EventMaker
from gosa.common.components import Plugin
from gosa.common.components import Command
from gosa.common import Environment
from gosa.common.components import PluginRegistry, AMQPServiceProxy
from gosa.common.components.amqp import AMQPHandler

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
        checksum, result = gosa_dbus.inventory(dbus_interface="com.gonicus.gosa")

        # Establish amqp connection
        env = Environment.getInstance()
        try:
            amqp = PluginRegistry.getInstance("AMQPHandler")
            proxy = AMQPServiceProxy(amqp.url['source'])
        except:
            proxy = AMQPServiceProxy('amqps://amqp:secret@amqp.intranet.gonicus.de:5671/org.gosa')

        proxy.sendEvent(result)
        return
