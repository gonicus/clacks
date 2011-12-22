# -*- coding: utf-8 -*-
import dbus
import StringIO
import hashlib
import re
import logging
from threading import Thread
from lxml import etree
from clacks.common.event import EventMaker
from clacks.common.components import Plugin
from clacks.common.components import Command
from clacks.common import Environment
from clacks.common.components import PluginRegistry, AMQPServiceProxy
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
        self.log = logging.getLogger(__name__)

    @Command()
    def request_inventory(self, old_checksum=None):
        """ Sent a notification to a given user """

        # Get BUS connection
        try:
            bus = dbus.SystemBus()
            gosa_dbus = bus.get_object('org.clacks', '/org/clacks/inventory')

            # Request inventory result from dbus-client (He is running as root and can do much more than we can)
            result = gosa_dbus.inventory(dbus_interface="org.clacks")

        except dbus.DBusException as e:
            self.log.debug("failed to call dbus method 'inventory': %s" % (str(e)))
            return False

        # Remove time base or frequently changing values (like processes) from the
        # result to generate a useable checksum.
        # We use a XSL file which reads the result and skips some tags.
        xml_doc = etree.parse(StringIO.StringIO(result))

        checksum_doc = etree.parse(resource_filename("clacks.client.plugins.inventory", "data/xmlToChecksumXml.xsl"))
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

        def runner():
            # Establish amqp connection
            amqp = PluginRegistry.getInstance("AMQPClientHandler")
            amqp.sendEvent(str(result))

        self.__thread = Thread(target=runner)
        self.__thread.start()
        return True
