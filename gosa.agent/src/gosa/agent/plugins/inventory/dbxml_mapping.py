# -*- coding: utf-8 -*-
import os
import logging
from dbxml import XmlManager, DBXML_ALLOW_EXTERNAL_ACCESS, XmlValue, DBXML_ALLOW_VALIDATION, XmlContainer
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


    def __init__(self, dbpath):
        """
        Creates and establishes a dbxml container connection.
        """

        self.dbpath = dbpath

        # Enable logging
        self.log = logging.getLogger(__name__)
        self.env = Environment.getInstance()

        # Ensure that the given dbpath is accessible
        if not os.path.exists(os.path.dirname(dbpath)):
            os.makedirs(os.path.dirname(dbpath))

        # External access is required to validate against a given xml-schema
        self.manager = XmlManager(DBXML_ALLOW_EXTERNAL_ACCESS)
        #self.manager.setLogLevel(LEVEL_INFO, True)

        # Create the update context, it is required to query and manipulate data later.
        self.updateContext = self.manager.createUpdateContext()

        # Create query context and set namespaces
        self.queryContext = self.manager.createQueryContext()
        self.queryContext.setNamespace("", "http://www.gonicus.de/Events")
        self.queryContext.setNamespace("gosa", "http://www.gonicus.de/Events")
        self.queryContext.setNamespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")

        # Set a variable named $doc which contains the path to the dbxml container
        # This make queries a lot shorter.
        self.queryContext.setVariableValue("doc", XmlValue("dbxml:///%s" % self.dbpath))

        # Let the user know that things went fine
        self.log.info("inventory database successfully initialized")

        # List all known inventory clients
        self.open()
        results = self.manager.query("collection($doc)/Event/Inventory/"
                "ClientUUID/text()", self.queryContext)
        results.reset()
        for value in results:
            self.log.debug("inventory database contains client-uuid %s'" % value.asString())

    def sync(self):
        """
        Syncs database changes back to the filesystem
        """
        self.log.debug("inventory database '%s' synced" % self.dbpath)
        self.container.sync()

    def close(self):
        """
        Closes the opened inventory container
        """
        self.log.debug("inventory database '%s' closed" % self.dbpath)
        self.container.close()

    def open(self):
        """
        Opens the inventory container file.
        """

        # Open (create) the database container
        if self.manager.existsContainer(self.dbpath) != 0:
            self.log.debug("inventory database '%s' opened" % self.dbpath)
            self.container = self.manager.openContainer(self.dbpath)
        else:
            self.log.debug("inventory database '%s' created and opened" % self.dbpath)
            self.container = self.manager.createContainer(self.dbpath, DBXML_ALLOW_VALIDATION, XmlContainer.NodeContainer)
