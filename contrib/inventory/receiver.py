#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, mapper, relationship, backref
from gosa.common.components import AMQPEventConsumer
from lxml import etree
from bsddb3.db import *
from dbxml import *
import sys


Base = declarative_base()
class Inventory(Base):

    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True)
    checksum = Column(String)
    uuid = Column(String)
    hostname = Column(String)
    content = Column(String)
    date = Column(DateTime)


class InventoryDBMySql(object):

    def __init__(self, base):
        self.engine = create_engine('sqlite:///:memory:', echo=True)
        #self.engine = create_engine('mysql://root:tester@gosa-playground-squeeze/tester', echo=True)
        base.metadata.create_all(self.engine)

    def deleteByUUID(self, uuid):
        """
        Removes an inventory entry by client-uuid.
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()

        # Should only be one, but to be sure - delete all occurrences
        for entry in  session.query(Client).filter_by(uuid=uuid).all():
            entry.delete()

        session.commit()


    def add(self, uuid, checksum, hostname, xml):
        """
        Removes an inventory entry by client-uuid.
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()

        c = Client()
        c.checksum = checksum
        c.uuid = uuid
        c.hostname = hostname
        c.content = xml
        c.date = datetime.datetime.today()

        session.add(c)
        session.commit()


class InventoryDBXml(object):
    """
    GOsa client-inventory database based on DBXML
    """

    dbname = None
    manager = None
    updateContext = None
    queryContext = None
    container = None

    def __init__(self, dbname="xmldb.xmldb"):
        """
        Creates and establishes a dbxml container connection.
        """

        # External access is required to validate against a given xml-schema
        self.manager = XmlManager(DBXML_ALLOW_EXTERNAL_ACCESS)

        # Create the database container on demand
        self.dbname = dbname
        if self.manager.existsContainer(self.dbname) != 0:
            self.container = self.manager.openContainer(self.dbname)
        else:
            self.container = self.manager.createContainer(self.dbname, DBXML_ALLOW_VALIDATION, XmlContainer.NodeContainer)

        # Create the update context, it is required to query and manipulate data later.
        self.updateContext = self.manager.createUpdateContext()

        # Create query context and set namespaces
        self.queryContext = self.manager.createQueryContext()
        self.queryContext.setNamespace("", "http://www.gonicus.de/Events")
        self.queryContext.setNamespace("gosa", "http://www.gonicus.de/Events")
        self.queryContext.setNamespace("xsi","http://www.w3.org/2001/XMLSchema-instance")

    def clientDataExists(self, uuid):
        """
        Checks whether an inventory exists for the given client ID or not.
        """
        #TODO: Use client-UUID to check for existing entries.
        results = self.manager.query("collection('%s')/Event/Inventory[DeviceID='%s']/DeviceID/string()" % (self.dbname, uuid), self.queryContext)
        results.reset()
        for value in results:
            return True
        return False

    def addClientInventoryData(self, uuid, data):
        """
        Adds client inventory data to the database.
        """
        self.container.putDocument(uuid, data, self.updateContext)


# --------------------------


class InventoryCosumer(object):
    """
    Consumer for inventory events emitted from clients.
    """

    xmldbname = "dbinv.dbmx"
    xmldb = None

    inv_db = None
    def __init__(self):
        self.xmldb = InventoryDBXml(self.xmldbname)
        self.mysqldb = InventoryDBMySql(Base)


    def process(self, data):
        """
        Receives a new inventory-event and updates the corresponding
        database entries (MySql and dbxml)
        """


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
