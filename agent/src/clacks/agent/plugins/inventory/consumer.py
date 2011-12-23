# -*- coding: utf-8 -*-
import logging
from lxml import etree
import pkg_resources
from zope.interface import implements
from clacks.common import Environment
from clacks.common.components import Plugin
from clacks.common.handler import IInterfaceHandler
from clacks.common.components.amqp import EventConsumer
from clacks.common.components.registry import PluginRegistry
from clacks.agent.objects import ObjectFactory


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

    db = None

    def __init__(self):
        # Enable logging
        self.log = logging.getLogger(__name__)
        self.env = Environment.getInstance()

    def serve(self):
        # Try to establish the database connections
        self.db = PluginRegistry.getInstance("XMLDBHandler")
        if not self.db.collectionExists("inventory"):
            sf = pkg_resources.resource_filename('clacks.agent', 'plugins/goto/data/events/Inventory.xsd')
            self.__factory = ObjectFactory.getInstance()
            self.db.createCollection("inventory",
                    {"e": "http://www.gonicus.de/Events"},
                    {"inventory.xsd":  open(sf).read()})

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
            binfo = data.xpath('/e:Event/e:Inventory', namespaces={'e': 'http://www.gonicus.de/Events'})[0]
            uuid = str(binfo['ClientUUID'])
            huuid = str(binfo['HardwareUUID'])
            checksum = str(binfo['Checksum'])
            self.log.debug("inventory information received for client %s" % uuid)

        except Exception as e:
            msg = "failed to extract information from received inventory data: %s" % str(e)
            self.log.error(msg)
            raise InventoryException(msg)

        # Get the Inventory part of the event only
        inv_only =  etree.tostring(data.xpath('/e:Event/e:Inventory', \
                namespaces={'e': 'http://www.gonicus.de/Events'})[0], pretty_print=True)

        # The given hardware-uuid is already part of our inventory database
        if self.hardwareUUIDExists(huuid):

            # Now check if the client-uuid for the given hardware-uuid has changed.
            # This is the case, when the same hardware is joined as new clacks-client again.
            # - In that case: drop the old entry and add the new one.
            if uuid != self.getClientUUIDByHardwareUUID(huuid):
                self.log.debug("replacing inventory information for %s" % uuid)
                self.deleteByHardwareUUID(huuid)
                self.addClientInventoryData(huuid, inv_only)

            # The client-uuid is still the same but the checksum has changed
            elif checksum != self.getChecksumByHardwareUUID(huuid):
                self.log.debug("updating inventory information for %s" % uuid)
                self.deleteByHardwareUUID(huuid)
                self.addClientInventoryData(huuid, inv_only)

            # The client-uuid and the checksums are still the same
            else:
                self.log.debug("inventory information still up to date for %s" % uuid)

        else:
            # A new client has send its inventory data - Import data into dbxml
            self.log.debug("adding inventory information %s" % uuid)
            self.addClientInventoryData(huuid, inv_only)

    def getClientUUIDByHardwareUUID(self, huuid):
        """
        Returns the ClientUUID used by the given HardwareUUID.
        """
        results = self.db.xquery("collection('inventory')/e:Inventory"
                "[e:HardwareUUID='%s']/e:ClientUUID/string()" % (huuid))

        # Walk through results and return the ClientUUID
        if len(results) == 1:
            return(results[0])
        else:
            raise InventoryException("No or more than one ClientUUID was found for HardwareUUID")

    def getChecksumByHardwareUUID(self, huuid):
        """
        Returns the checksum of a specific entry.
        """
        results = self.db.xquery("collection('inventory')/e:Inventory"
                "[e:HardwareUUID='%s']/e:Checksum/string()" % (huuid))

        # Walk through results and return the found checksum
        if len(results) == 1:
            return(results[0])
        else:
            print results
            raise InventoryException("No or more than one checksums found for ClientUUID=%s" % (uuid))

    def hardwareUUIDExists(self, huuid):
        """
        Checks whether an inventory exists for the given client ID or not.
        """
        results = self.db.xquery("collection('inventory')/e:Inventory"
                "[e:HardwareUUID='%s']/e:HardwareUUID/string()" % (huuid))

        # Walk through results if there are any and return True in that case.
        return(len(results) != 0)

    def addClientInventoryData(self, huuid, data):
        """
        Adds client inventory data to the database.
        """
        self.db.addDocument('inventory', huuid, data)

    def deleteByHardwareUUID(self, huuid):
        results = self.db.xquery("collection('inventory')/e:Inventory"
                "[e:HardwareUUID='%s']" % (huuid))
        if len(results) == 1:
            self.db.deleteDocument('inventory', huuid)
        else:
            raise InventoryException("No or more than one document found, removal aborted!")
        return None


