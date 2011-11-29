# -*- coding: utf-8 -*-
import dbus
import StringIO
import hashlib
import re
from threading import Thread
from lxml import etree
from gosa.common.event import EventMaker
from gosa.common.components import Plugin
from gosa.common.components import Command
from gosa.common import Environment
from gosa.common.components import PluginRegistry, AMQPServiceProxy
from pkg_resources import resource_filename


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
    def request_inventory(self, old_checksum=None):

        """ Sent a notification to a given user """

        def runner():
            # Get BUS connection
            bus = dbus.SystemBus()
            gosa_dbus = bus.get_object('com.gonicus.gosa', '/com/gonicus/gosa/inventory')

            # Request inventory result from dbus-client (He is running as root and can do much more than we can)
            result = gosa_dbus.inventory(dbus_interface="com.gonicus.gosa")

            # Remove time base or frequently changing values (like processes) from the
            # result to generate a useable checksum.
            # We use a XSL file which reads the result and skips some tags.
            xml_doc = etree.parse(StringIO.StringIO(result))

            checksum_doc = etree.parse(resource_filename("gosa.dbus",'plugins/inventory/xmlToChecksumXml.xsl'))
            check_trans = etree.XSLT(checksum_doc)
            checksum_result = check_trans(xml_doc)

            # Once we've got a 'clean' result, create the checksum.
            m = hashlib.md5()
            m.update(etree.tostring(checksum_result))
            checksum = m.hexdigest()

            # Just don't do anything with the remote if the checksum did
            # not change
            if checksum == old_checksum:
                return

            # Insert the checksum into the resulting event
            result = re.sub(r"%%CHECKSUM%%", checksum, result)

            # Establish amqp connection
            amqp = PluginRegistry.getInstance("AMQPClientHandler")
            amqp.sendEvent(str(result))

        self.__thread = Thread(target=runner)
        self.__thread.start()
