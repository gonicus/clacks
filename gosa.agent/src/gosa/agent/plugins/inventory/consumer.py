#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import StringIO
import logging
from dbxml import *
from bsddb3.db import *
from lxml import etree, objectify
from gosa.common import Environment
from gosa.common.components import AMQPEventConsumer, Plugin
from gosa.common.components.amqp import EventConsumer
from gosa.common.components.registry import PluginRegistry
from gosa.agent.plugins.inventory.dbxml import InventoryDBXml



class InventoryException(Exception):
    """
    Inventory exception class
    """
    pass


class InventoryConsumer(Plugin):
    """
    Consumer for inventory events emitted from clients.
    """

    _target_ = 'inventory'

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
        self.log.info("Client-inventory databases successfully initialized")

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
        self.log.debug("New incoming client inventory event")
        try:
            binfo = data.xpath('/gosa:Event/gosa:Inventory', namespaces={'gosa': 'http://www.gonicus.de/Events'})[0]
            hostname = str(binfo['Hostname'])
            uuid = str(binfo['ClientUUID'])
            checksum = str(binfo['GOsaChecksum'])
            self.log.debug("Client inventory event received for hostname %s (%s)" % (hostname, uuid))
        except Exception as e:
            msg = "Failed extract client info out of received Inventory-Event! Error was: %s" % (str(e), )
            self.log.error(msg)
            raise InventoryException(msg)

        # The client is already part of our inventory database
        if self.xmldb.uuidExists(uuid):

            # Now check if the checksums match or if we've to update our databases
            if checksum == self.xmldb.getChecksumByUuid(uuid):
                self.log.debug("Client record already exists and checksums (%s) are equal, skipping addition." % (checksum))
            else:
                self.log.debug("Client record already exists but the checksum had changed, updated entry.")
                self.xmldb.deleteByUUID(uuid)
                datas = etree.tostring(data, pretty_print=True)
                self.xmldb.addClientInventoryData(uuid, datas)
        else:

            # A new client has send its inventory data - Import data into dbxml
            self.log.debug("Client record is new and will be added!")
            datas = etree.tostring(data, pretty_print=True)
            self.xmldb.addClientInventoryData(uuid, datas)
