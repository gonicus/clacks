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

Base = declarative_base()


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


    def add(self, uuid, checksum, hostname, xml):
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
            ret.append(entry.content)
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

    def __init__(self, dbname=r"xmldb.xmldb"):
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


class InventoryConsumer(object):
    """
    Consumer for inventory events emitted from clients.
    """

    xmldbname = r"dbinv.dbxml"
    xmldb = None

    inv_db = None
    def __init__(self):
        self.xmldb = InventoryDBXml(self.xmldbname)
        self.mysqldb = InventoryDBMySql(Base)

        xml_list = self.mysqldb.listAll()
        for entry in xml_list:

            # Try to extract the clients uuid and hostname out of the received data
            data = objectify.parse(StringIO.StringIO(entry))
            binfo = data.xpath('/gosa:Event/gosa:Inventory', namespaces={'gosa': 'http://www.gonicus.de/Events'})[0]
            uuid = str(binfo['ClientUUID'])

            # Add data read from mysql db
            print "Adding ... ", uuid
            datas = etree.tostring(data, pretty_print=True)
            self.xmldb.addClientInventoryData(uuid, datas)

    def process(self, data):
        """
        Receives a new inventory-event and updates the corresponding
        database entries (MySql and dbxml)
        """

        # Try to extract the clients uuid and hostname out of the received data
        binfo = data.xpath('/gosa:Event/gosa:Inventory', namespaces={'gosa': 'http://www.gonicus.de/Events'})[0]
        hostname = str(binfo['Hostname'])
        uuid = str(binfo['ClientUUID'])
        checksum = str(binfo['GOsaChecksum'])

        # Check if the given uuid is already part of the inventory database
        if self.xmldb.uuidExists(uuid):
            # check checksums.
            print "Schon da", hostname
            if checksum == self.xmldb.getChecksumByUuid(uuid):
                print "Gleich!"
            else:
                print "Updated!"
                self.mysqldb.deleteByUUID(uuid)
                self.xmldb.deleteByUUID(uuid)
                datas = etree.tostring(data, pretty_print=True)
                self.xmldb.addClientInventoryData(uuid, datas)
                self.mysqldb.add(uuid, checksum, hostname, datas)

        else:
            # import data to both dbxml and mysql
            print "Add", hostname
            datas = etree.tostring(data, pretty_print=True)
            self.xmldb.addClientInventoryData(uuid, datas)
            self.mysqldb.add(uuid, checksum, hostname, datas)


# Create event consumer
c = InventoryConsumer()
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
