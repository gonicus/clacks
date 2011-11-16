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
from base64 import b64decode
from Crypto.Cipher import AES


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


    def __init__(self, skip_serve=False):
        # Enable logging
        self.log = logging.getLogger(__name__)
        self.env = Environment.getInstance()

        # Try to establish the database connections
        self.xmldb = InventoryDBXml(self.env.config.get("inventory.dbpath", "/var/lib/gosa/inventory/db.dbxml"))

        # Let the user know that things went fine
        self.log.info("inventory databases successfully initialized")

        # Create event consumer
        if not skip_serve:
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
            huuid = str(binfo['HardwareUUID'])
            checksum = str(binfo['GOsaChecksum'])
            self.log.debug("inventory event received for hostname %s (%s)" % (hostname, uuid))

        except Exception as e:
            msg = "failed extract client info out of received Inventory event: %s" % str(e)
            self.log.error(msg)
            raise InventoryException(msg)

        #TODO: Use the clients real hardware uuid - I dont't know how to get it.
        chuuid = "8C492981-4A82-11CB-B73B-FB1675859266"

        # Decode received hardware uuid
        huuid = self.decodeHardwareUUID(chuuid.replace("-", ""), huuid)

        # The given hardware-uuid is already part of our inventory database
        if self.xmldb.hardwareUUIDExists(huuid):

            # Now check if the client-uuid for the given hardware-uuid has changed.
            # This is the case, when the same hardware is joined as new gosa-client again.
            # - In that case: drop the old entry and add the new one.
            if uuid != self.xmldb.getClientUUIDByHardwareUUID(huuid):
                self.log.debug("record for '%s' with uuid (%s) already exists but hardware-uuid has changed"
                        " - removing old entry and adding new one" % (hostname, uuid))
                self.xmldb.deleteByHardwareUUID(huuid)
                datas = etree.tostring(data, pretty_print=True)
                self.xmldb.addClientInventoryData(uuid, huuid, datas)

            # The client-uuid is still the same
            else:

                # Now check if the checksums match or if we've to update our databases
                if checksum == self.xmldb.getChecksumByUUID(uuid):
                    self.log.debug("record for '%s' with uuid (%s) already exists and checksums are equal"
                            " - entry up to date" % (hostname, uuid))
                else:
                    self.log.debug("record for '%s' with uuid (%s) already exists but the checksum has changed"
                            " - updating entry" % (hostname, uuid))
                    self.xmldb.deleteByHardwareUUID(huuid)
                    datas = etree.tostring(data, pretty_print=True)
                    self.xmldb.addClientInventoryData(uuid, huuid, datas)

        else:
            # A new client has send its inventory data - Import data into dbxml
            self.log.debug("adding new record for '%s' with uuid (%s)" % (hostname, uuid))
            datas = etree.tostring(data, pretty_print=True)
            self.xmldb.addClientInventoryData(uuid, huuid, datas)

    def decodeHardwareUUID(self, key, data):
        """
        Decodes the received HardwareUUID string
        """
        data = b64decode(data)
        key_pad = AES.block_size - len(key) % AES.block_size
        if key_pad != AES.block_size:
            key += chr(key_pad) * key_pad
        data = AES.new(key, AES.MODE_ECB).decrypt(data)
        return data[20:-ord(data[-1])]


