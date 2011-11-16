# -*- coding: utf-8 -*-
import logging
from dbxml import *
from bsddb3.db import *
from lxml import etree
from gosa.common import Environment
from gosa.common.components import Plugin
from gosa.common.components.amqp import EventConsumer
from gosa.common.components.registry import PluginRegistry
from gosa.agent.plugins.inventory.dbxml_mapping import InventoryDBXml


class InventoryException(Exception):
    pass


class InventoryConsumer(Plugin):
    """
    Consumer for inventory events emitted from clients.
    """
    _target_ = 'inventory'
    _priority_ = 92

    xmldb = None
    log = None
    inv_db = None


    def __init__(self):
        # Enable logging
        self.log = logging.getLogger(__name__)
        self.env = Environment.getInstance()

        # Try to establish the database connections
        self.xmldb = InventoryDBXml(self.env.config.get("inventory.dbpath", "/var/lib/gosa/inventory/db.dbxml"))

        # Let the user know that things went fine
        self.log.info("inventory databases successfully initialized")

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

    def process(self, data):
        """
        Receives a new inventory-event and updates the corresponding
        database entries (MySql and dbxml)
        """

        # Try to extract the clients uuid and hostname out of the received data
        self.log.debug("new incoming client inventory event")
        try:
            binfo = data.xpath('/gosa:Event/gosa:Inventory', namespaces={'gosa': 'http://www.gonicus.de/Events'})[0]
            hostname = str(binfo['Hostname'])
            uuid = str(binfo['ClientUUID'])
            checksum = str(binfo['GOsaChecksum'])
            self.log.debug("inventory event received for hostname %s (%s)" % (hostname, uuid))

        except Exception as e:
            msg = "failed extract client info out of received Inventory event: %s" % str(e)
            self.log.error(msg)
            raise InventoryException(msg)

        # The client is already part of our inventory database
        if self.xmldb.uuidExists(uuid):

            # Now check if the checksums match or if we've to update our databases
            if checksum == self.xmldb.getChecksumByUuid(uuid):
                self.log.debug("record already exists and checksums (%s) are equal - entry up to date" % checksum)
            else:
                self.log.debug("record already exists but the checksum has changed - updating entry")
                self.xmldb.deleteByUUID(uuid)
                datas = etree.tostring(data, pretty_print=True)
                self.xmldb.addClientInventoryData(uuid, datas)

        else:
            # A new client has send its inventory data - Import data into dbxml
            self.log.debug("adding new record for %s" % uuid)
            datas = etree.tostring(data, pretty_print=True)
            self.xmldb.addClientInventoryData(uuid, datas)
