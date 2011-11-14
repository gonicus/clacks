#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bsddb3.db import *
from dbxml import *
import sys


class InventoryDB(object):
    """
    GOsa client-inventory database based on DBXML
    """

    dbname = "dbinv.dbmx"
    manager = None
    updateContext = None
    queryContext = None
    container = None

    def __init__(self):
        """
        Creates and establishes a dbxml container connection.
        """

        # External access is required to validate against a given xml-schema
        self.manager = XmlManager(DBXML_ALLOW_EXTERNAL_ACCESS)

        # Create the database container on demand
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


db = InventoryDB()
if not db.clientDataExists('garnele'):
    db.addClientInventoryData('garnele', open('data/xml_content.xml').read())
if not db.clientDataExists('independence'):
    db.addClientInventoryData('independence', open('data/xml_content2.xml').read())



