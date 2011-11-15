#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, mapper, relationship, backref
from gosa.common.components import AMQPEventConsumer
from lxml import etree, objectify
from bsddb3.db import *
from dbxml import *
import os
import sys
import StringIO
import datetime
import logging

Base = declarative_base()


class InventoryException(Exception):
    pass


class Inventory(Base):
    __tablename__ = 'inventory'
    id = Column(Integer, primary_key=True)
    checksum = Column(String(255))
    uuid = Column(String(255))
    hostname = Column(String(255))
    content = Column('content', Text(4294967295), nullable=False)
    date = Column(DateTime)


class InventoryDBMySql(object):

    def __init__(self, base):
        #self.engine = create_engine('sqlite:///:memory:', echo=True)
        self.engine = create_engine('mysql://root:tester@gosa-playground-squeeze/tester', echo=False)
        base.metadata.create_all(self.engine)

    def deleteByUUID(self, uuid):
        """
        Removes an inventory entry by client-uuid.
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()

        # Should only be one, but to be sure - delete all occurrences
        for entry in  session.query(Inventory).filter_by(uuid=uuid).all():
            session.delete(entry)

        session.commit()


    def addClientInventoryData(self, uuid, checksum, hostname, xml):
        """
        Removes an inventory entry by client-uuid.
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()

        c = Inventory()
        c.checksum = checksum
        c.uuid = uuid
        c.hostname = hostname
        c.content = xml
        c.date = datetime.datetime.today()

        session.add(c)
        session.commit()

    def listAll(self):
        """
        Returns a list with all inventory information
        """
        ret = []
        Session = sessionmaker(bind=self.engine)
        session = Session()
        for entry in session.query(Inventory).all():
            ret.append((entry.content, entry.id))
        return(ret)


class InventoryDBXml(object):
    """
    GOsa client-inventory database based on DBXML
    """

    dbname = None
    manager = None
    updateContext = None
    queryContext = None
    container = None

    def __init__(self, dbname):
        """
        Creates and establishes a dbxml container connection.
        """

        # External access is required to validate against a given xml-schema
        self.manager = XmlManager(DBXML_ALLOW_EXTERNAL_ACCESS)

        # Create the database container on demand
        self.dbname = dbname

        #TODO: Check why the 'existsContainer' does not work and then remove the os.path check.
        if os.path.exists(self.dbname) or self.manager.existsContainer(self.dbname) != 0:
            self.manager.removeContainer(self.dbname)
        self.container = self.manager.createContainer(self.dbname, DBXML_ALLOW_VALIDATION)

        # Create the update context, it is required to query and manipulate data later.
        self.updateContext = self.manager.createUpdateContext()

        # Create query context and set namespaces
        self.queryContext = self.manager.createQueryContext()
        self.queryContext.setNamespace("", "http://www.gonicus.de/Events")
        self.queryContext.setNamespace("gosa", "http://www.gonicus.de/Events")
        self.queryContext.setNamespace("xsi","http://www.w3.org/2001/XMLSchema-instance")

    def uuidExists(self, uuid):
        """
        Checks whether an inventory exists for the given client ID or not.
        """
        results = self.manager.query("collection('%s')/Event/Inventory[ClientUUID='%s']/ClientUUID/string()" % (self.dbname, uuid), self.queryContext)
        results.reset()
        for value in results:
            print value.asString()
            return True
        return False

    def getChecksumByUuid(self, uuid):
        """
        Returns the checksum of a specific entry.
        """
        results = self.manager.query("collection('%s')/Event/Inventory[ClientUUID='%s']/GOsaChecksum/string()" % (self.dbname, uuid), self.queryContext)
        results.reset()
        for value in results:
            return value.asString()
        return None

    def addClientInventoryData(self, uuid, data):
        """
        Adds client inventory data to the database.
        """
        self.container.putDocument(uuid, data, self.updateContext)

    def deleteByUUID(self, uuid):
        results = self.manager.query("collection('%s')/Event/Inventory[ClientUUID='%s']" % (self.dbname, uuid), self.queryContext)
        results.reset()
        for value in results:
            self.container.deleteDocument(value.asDocument().getName(), self.updateContext)
        return None

# --------------------------


class InventoryCosumer(object):
    """
    Consumer for inventory events emitted from clients.
    """

    xmldbname = r"dbinv.dbxml"
    xmldb = None
    log = None

    inv_db = None
    def __init__(self):

        # Enable logging
        self.log = logging.getLogger(__name__)

        # Try to establish the database connections
        self.log.debug("Initializing client-inventory databases")
        self.xmldb = InventoryDBXml(self.xmldbname)
        self.mysqldb = InventoryDBMySql(Base)
        self.log.debug("Initializing client-inventory databases - done!")

        # Load all existing inventory entries from the MySql database and put them into them
        # dbxml database
        xml_list = self.mysqldb.listAll()
        self.log.debug("Found %s existing client inventory data sets" % (len(xml_list),))
        for entry, eid in xml_list:

            # Try to extract the clients uuid and hostname out of the received data
            self.log.debug("Try to add client inventory data set with id %s" % (eid,))
            try:
                data = objectify.parse(StringIO.StringIO(entry))
                binfo = data.xpath('/gosa:Event/gosa:Inventory', namespaces={'gosa': 'http://www.gonicus.de/Events'})[0]
                uuid = str(binfo['ClientUUID'])
                hostname = str(binfo['Hostname'])
            except Exception as e:
                self.log.error("Failed to read MySql inventory entry with id '%s', error was: %s" % (eid, str(e)))
                raise InventoryException("Failed to read MySql inventory entry with id '%s', error was: %s" % (eid, str(e)))

            # Add data read from mysql db
            self.log.debug("Adding inventory data for '%s' from MySql database ..." % (hostname))
            try:
                datas = etree.tostring(data, pretty_print=True)
                self.xmldb.addClientInventoryData(uuid, datas)
            except Exception as e:
                self.log.error("Failed to import MySql inventory entry with id '%s', error was: %s" % (eid, str(e)))
                raise InventoryException("Failed to import MySql inventory entry with id '%s', error was: %s" % (eid, str(e)))

        # Let the user know that things went fine
        self.log.info("Client-inventory databases successfully initialized")

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
            self.log.debug("Client inventory event received for hostname %s (%s)" % (hostname,uuid))
        except Exception as e:
            msg = "Failed extract client info out of received Inventory-Event! Error was: %s" % (str(e),)
            self.log.error(msg)
            raise InventoryException(msg)

        # The client is already part of our inventory database
        if self.xmldb.uuidExists(uuid):

            # Now check if the checksums match or if we've to update our databases
            if checksum == self.xmldb.getChecksumByUuid(uuid):
                self.log.debug("Client data set already exists and checksums (%s) are equal, skipping addition!" % (checksum))
            else:
                self.log.debug("Client data set already exists but the checksum had changed, updated entry!" % (checksum))
                self.mysqldb.deleteByUUID(uuid)
                self.xmldb.deleteByUUID(uuid)
                datas = etree.tostring(data, pretty_print=True)
                self.xmldb.addClientInventoryData(uuid, datas)
                self.mysqldb.addClientInventoryData(uuid, checksum, hostname, datas)
        else:

            # A new client has send its inventory data - Import data to both dbxml and mysql
            self.log.debug("Client data set is new and will be added!" % (checksum))
            datas = etree.tostring(data, pretty_print=True)
            self.xmldb.addClientInventoryData(uuid, datas)
            self.mysqldb.addClientInventoryData(uuid, checksum, hostname, datas)


# Create event consumer
c = InventoryCosumer()
consumer = AMQPEventConsumer("amqps://amqp:secret@amqp.intranet.gonicus.de:5671/org.gosa",
            xquery="""
                declare namespace f='http://www.gonicus.de/Events';
                let $e := ./f:Event
                return $e/f:Inventory
            """,
            callback=c.process)

# Main loop, process threads
try:
    while True:
        consumer.join()
except KeyboardInterrupt:
    del consumer
    exit(0)
