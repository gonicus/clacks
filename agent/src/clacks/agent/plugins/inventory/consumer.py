# -*- coding: utf-8 -*-
import logging
from zope.interface import implements
from clacks.common import Environment
from clacks.common.utils import xml2dict
from clacks.common.components import Plugin
from clacks.common.handler import IInterfaceHandler
from clacks.common.components.amqp import EventConsumer
from clacks.common.components.registry import PluginRegistry


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

    log = None
    inv_db = None

    db = None

    def __init__(self):
        # Enable logging
        self.log = logging.getLogger(__name__)
        self.env = Environment.getInstance()

    def serve(self):
        # Establish the database connection
        self.db = self.env.get_mongo_db("clacks").inventory

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

        # Register a listener for potential client registries
        cs = PluginRegistry.getInstance("ClientService")
        cs.register_listener('request_inventory', self.client_listener)

    def client_listener(self, client, method, mode):
        if mode:
            # Send an inventory information with the current checksum
            self.log.info("requesting inventory from client %s" % client)
            cs = PluginRegistry.getInstance("ClientService")

            entry = self.db.find_one({'ClientUUID': client}, {'Checksum': 1})
            if entry:
                cs.clientDispatch(client, "request_inventory", entry['Checksum'])
            else:
                cs.clientDispatch(client, "request_inventory")

    def process(self, data):
        """
        Receives a new inventory-event and updates the corresponding
        database entries (MySql and dbxml)
        """

        # Try to extract the clients uuid and hostname out of the received data
        try:
            binfo = data.xpath('/e:Event/e:Inventory', namespaces={'e': 'http://www.gonicus.de/Events'})[0]
            uuid = binfo['ClientUUID'].text
            huuid = binfo['HardwareUUID'].text
            checksum = binfo['Checksum'].text
            self.log.debug("inventory information received for client %s" % uuid)

        except Exception as e:
            msg = "failed to extract information from received inventory data: %s" % str(e)
            self.log.error(msg)
            raise InventoryException(msg)

        # Get the Inventory part of the event only
        inv_only = xml2dict(data.xpath('/e:Event/e:Inventory', \
                namespaces={'e': 'http://www.gonicus.de/Events'})[0])

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
            # A new client has send its inventory data - Import data into mongodb
            self.log.debug("adding inventory information %s" % uuid)
            self.addClientInventoryData(huuid, inv_only)

    def getClientUUIDByHardwareUUID(self, huuid):
        """
        Returns the ClientUUID used by the given HardwareUUID.
        """
        results = self.db.find({'HardwareUUID': huuid}, {'ClientUUID': 1})

        # Walk through results and return the ClientUUID
        if results.count() == 1:
            return(results[0]['ClientUUID'])
        else:
            raise InventoryException("No or more than one ClientUUID was found for HardwareUUID")

    def getChecksumByHardwareUUID(self, huuid):
        """
        Returns the checksum of a specific entry.
        """
        results = self.db.find({'HardwareUUID': huuid}, {'Checksum': 1})

        # Walk through results and return the found checksum
        if results.count() == 1:
            return(results[0]['Checksum'])
        else:
            raise InventoryException("No or more than one checksums found for ClientUUID=%s" % huuid)

    def hardwareUUIDExists(self, huuid):
        """
        Checks whether an inventory exists for the given client ID or not.
        """
        return bool(self.db.find_one({'HardwareUUID': huuid}, {'HardwareUUID': 1}))

    def addClientInventoryData(self, huuid, data):
        """
        Adds client inventory data to the database.
        """
        if self.hardwareUUIDExists(huuid):
            self.db.remove({'HardwareUUID': huuid})

        self.db.save(data)

    def deleteByHardwareUUID(self, huuid):
        if self.hardwareUUIDExists(huuid):
            self.db.remove({'HardwareUUID': huuid})
