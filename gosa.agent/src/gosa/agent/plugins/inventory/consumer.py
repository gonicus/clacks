# -*- coding: utf-8 -*-
import logging
from dbxml import *
from lxml import etree
from zope.interface import implements
from gosa.common import Environment
from gosa.common.components import Plugin
from gosa.common.handler import IInterfaceHandler
from gosa.common.components.amqp import EventConsumer
from gosa.common.components.registry import PluginRegistry
from gosa.agent.plugins.inventory.dbxml_mapping import InventoryDBXml


class InventoryException(Exception):
    pass


class InventoryConsumer(Plugin):
    """
    Consumer for inventory events emitted from clients.
    """
    implements(IInterfaceHandler)

    # Leave this in core as long we've no @Command
    _target_ = 'core'
    _priority_ = 92

    xmldb = None
    log = None
    inv_db = None


    def __init__(self):
        # Enable logging
        self.log = logging.getLogger(__name__)
        self.env = Environment.getInstance()

        # Try to establish the database connections
        path = self.env.config.get("inventory.dbpath", "/var/lib/gosa/inventory/db.dbxml")
        self.xmldb = InventoryDBXml(path)

    def serve(self):
        # Create event consumer
        amqp = PluginRegistry.getInstance('AMQPHandler')
        EventConsumer(self.env,
            amqp.getConnection(),
            xquery="""
                declare namespace f='http://www.gonicus.de/Events';
                let $e := ./f:Event
                return $e/f:Inventory
            """,
            callback=self.process)

        self.log.info("listening for incoming inventory notifications")

    def process(self, data):
        """
        Receives a new inventory-event and updates the corresponding
        database entries (MySql and dbxml)
        """

        # Try to extract the clients uuid and hostname out of the received data
        try:
            binfo = data.xpath('/gosa:Event/gosa:Inventory', namespaces={'gosa': 'http://www.gonicus.de/Events'})[0]
            uuid = str(binfo['ClientUUID'])
            huuid = str(binfo['HardwareUUID'])
            checksum = str(binfo['GOsaChecksum'])
            self.log.debug("inventory information received for client %s" % uuid)

        except Exception as e:
            msg = "failed to extract information from received inventory data: %s" % str(e)
            self.log.error(msg)
            raise InventoryException(msg)

        # The given hardware-uuid is already part of our inventory database
        self.xmldb.open()
        if self.xmldb.hardwareUUIDExists(huuid):

            # Now check if the client-uuid for the given hardware-uuid has changed.
            # This is the case, when the same hardware is joined as new gosa-client again.
            # - In that case: drop the old entry and add the new one.
            if uuid != self.xmldb.getClientUUIDByHardwareUUID(huuid):
                self.log.debug("replacing inventory information for %s" % uuid)
                self.xmldb.deleteByHardwareUUID(huuid)
                datas = etree.tostring(data, pretty_print=True)
                self.xmldb.addClientInventoryData(uuid, huuid, datas)

            # The client-uuid is still the same
            elif checksum != self.xmldb.getChecksumByUUID(uuid):
                self.log.debug("updating inventory information for %s" % uuid)
                self.xmldb.deleteByHardwareUUID(huuid)
                datas = etree.tostring(data, pretty_print=True)
                self.xmldb.addClientInventoryData(uuid, huuid, datas)

        else:
            # A new client has send its inventory data - Import data into dbxml
            self.log.debug("adding inventory information %s" % uuid)
            datas = etree.tostring(data, pretty_print=True)
            self.xmldb.addClientInventoryData(uuid, huuid, datas)

        # Sync database container - things will not work without it - even the database cannot be opened again
        self.xmldb.sync()
