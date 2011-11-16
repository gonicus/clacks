#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from dbxml import *
from bsddb3.db import *
from lxml import etree, objectify
from gosa.common import Environment


class InventoryDBXml(object):
    """
    GOsa client-inventory database based on DBXML
    """

    dbpath = None
    manager = None
    updateContext = None
    queryContext = None
    container = None
    env = None
    log = None

    def __init__(self, dbpath):
        """
        Creates and establishes a dbxml container connection.
        """

        # Enable logging
        self.log = logging.getLogger(__name__)
        self.env = Environment.getInstance()

        # Ensure that the given dbpath is accessible
        if not os.path.exists(os.path.dirname(dbpath)):
            os.makedirs(os.path.dirname(dbpath))

        # External access is required to validate against a given xml-schema
        self.manager = XmlManager(DBXML_ALLOW_EXTERNAL_ACCESS)

        # Open (create) the database container
        self.container = self.manager.openContainer(dbpath, DB_CREATE|DBXML_ALLOW_VALIDATION)
        self.dbpath = "dbxml:///%s" % (dbpath,)

        # Create the update context, it is required to query and manipulate data later.
        self.updateContext = self.manager.createUpdateContext()

        # Create query context and set namespaces
        self.queryContext = self.manager.createQueryContext()
        self.queryContext.setNamespace("", "http://www.gonicus.de/Events")
        self.queryContext.setNamespace("gosa", "http://www.gonicus.de/Events")
        self.queryContext.setNamespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")

    def uuidExists(self, uuid):
        """
        Checks whether an inventory exists for the given client ID or not.
        """
        results = self.manager.query("collection('%s')/Event/Inventory[ClientUUID='%s']/ClientUUID/string()" % (
            self.dbpath, uuid), self.queryContext)

        # Walk through results if there are any and return True in that case.
        results.reset()
        for value in results:
            return True
        return False

    def getChecksumByUuid(self, uuid):
        """
        Returns the checksum of a specific entry.
        """
        results = self.manager.query("collection('%s')/Event/Inventory[ClientUUID='%s']/GOsaChecksum/string()" % (
            self.dbpath, uuid), self.queryContext)

        # Walk through results and return the found checksum
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
        results = self.manager.query("collection('%s')/Event/Inventory[ClientUUID='%s']" % (self.dbpath, uuid), self.queryContext)
        results.reset()
        for value in results:
            self.container.deleteDocument(value.asDocument().getName(), self.updateContext)
        return None
