# -*- coding: utf-8 -*-
import dbus
import StringIO
import hashlib
from lxml import etree
from gosa.common.event import EventMaker
from gosa.common.components import Plugin
from gosa.common.components import Command
from gosa.common import Environment
from gosa.common.components import PluginRegistry, AMQPServiceProxy
from gosa.common.components.amqp import AMQPHandler
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
    def request_inventory(self):

        """ Sent a notification to a given user """

        # Get BUS connection
        bus = dbus.SystemBus()
        gosa_dbus = bus.get_object('com.gonicus.gosa', '/com/gonicus/gosa/inventory')

        #print "FIXME: client directly load dummy result insted of calling a dbus method!"
        #result = open('/home/hickert/gosa-ng/src/contrib/inventory/dummy.xml').read()

        # # Request inventory result from dbus-client (He is running as root and can do much more than we can)
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

        # Insert the checksum into the resulting event
        result = result % {'GOsa_Checksum': checksum}

        # Establish amqp connection
        env = Environment.getInstance()
        try:
            amqp = PluginRegistry.getInstance("AMQPHandler")
            proxy = AMQPServiceProxy(amqp.url['source'])
        except:
            proxy = AMQPServiceProxy('amqps://amqp:secret@amqp.intranet.gonicus.de:5671/org.gosa')

        proxy.sendEvent(result)
        return
