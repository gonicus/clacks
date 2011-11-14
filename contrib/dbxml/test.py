#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bsddb3.db import *
from dbxml import *

import sys
if __name__ == "__main__":

    containerName = r"database.dbxml"

    # External access is required to validate against a given xml-schema
    mgr = XmlManager(DBXML_ALLOW_EXTERNAL_ACCESS)

    #if mgr.existsContainer(containerName) != 0:
    #    mgr.removeContainer(containerName)

    # Create the update context, it is required to query and manipulate data later.
    uc = mgr.createUpdateContext()

    # Create the database container on demand
    if mgr.existsContainer(containerName) != 0:
        print "XML DB existiert bereits!"
        cont = mgr.openContainer(containerName)
    else:
        print "XML DB erstellt!"
        cont = mgr.createContainer(containerName, DBXML_ALLOW_VALIDATION, XmlContainer.NodeContainer)
        cont.putDocument(r"garnele", open('data/xml_content.xml').read(), uc)
        cont.putDocument(r"independence", open('data/xml_content2.xml').read(), uc)

    # Create query context and populate used namespaces
    qc = mgr.createQueryContext()
    qc.setNamespace("", "http://www.gonicus.de/Events")
    qc.setNamespace("gosa", "http://www.gonicus.de/Events")
    qc.setNamespace("xsi","http://www.w3.org/2001/XMLSchema-instance")

    # Query for the used DeviceIDs
    print
    print "Searching for client-inventory data ..."
    results = mgr.query("collection('%s')/Event/Inventory/DeviceID/string()" % (containerName,), qc)
    results.reset()
    print "Found client inventory data sets for:"
    for value in results:
        print " * %s" % (value.asString(),)
        DeviceID=value.asString()

        # Query for garneles
        cversion = mgr.query("collection('%s')/Event/Inventory[DeviceID='%s']/ClientVersion/string()" % (containerName, DeviceID,), qc)
        cversion.reset()
        for value in cversion:
            print "   is using client version: %s" % (value.asString(),)

    # Remove garnele from the collection add re-add it
    cont.deleteDocument(r"garnele", uc)
    cont.putDocument(r"garnele", open('data/xml_content.xml').read(), uc)

    # Query for the used DeviceIDs
    print "\nListing DeviceIDs"
    results = mgr.query("collection('%s')/Event/Inventory/DeviceID/string()" % (containerName,), qc)
    results.reset()
    print "Found client inventory data sets for:"
    for value in results:
        print " * %s" % (value.asString(),)

    # Update the DeviceID of garnele to dummy
    print "\nUpdating DeviceID of garnele to Dummy"
    mgr.query("replace value of node collection('%s')/Event/Inventory[DeviceID='garnele']/DeviceID with 'Dummy'" % (containerName,), qc)

    # Query for the used DeviceIDs
    print "\nListing DeviceIDs"
    results = mgr.query("collection('%s')/Event/Inventory/DeviceID/string()" % (containerName,), qc)
    results.reset()
    print "Found client inventory data sets for:"
    for value in results:
        print " * %s" % (value.asString(),)
