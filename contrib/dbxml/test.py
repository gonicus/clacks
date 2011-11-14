#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bsddb3.db import *
from dbxml import *

import sys
if __name__ == "__main__":

    containerName = r"inventory.dbxml"

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
        cont.putDocument(r"garnele-2011-10-27-16-23-21", open('data/xml_content.xml').read(), uc)
        cont.putDocument(r"independence-2011-10-27-16-19-50", open('data/xml_content2.xml').read(), uc)

    # Create query context and populate used namespaces
    qc = mgr.createQueryContext()
    qc.setNamespace("", "http://www.gonicus.de/Events")
    qc.setNamespace("gosa", "http://www.gonicus.de/Events")
    qc.setNamespace("xsi","http://www.w3.org/2001/XMLSchema-instance")

    # Query for the used DeviceIDs
    print
    print "Searching for client-inventory data ..."
    results = mgr.query("collection('inventory.dbxml')/Event/Inventory/DeviceID/string()", qc)
    results.reset()
    print "Found client inventory data sets for:"
    for value in results:
        print " * %s" % (value.asString(),)
        DeviceID=value.asString()

        # Query for garneles
        cversion = mgr.query("collection('inventory.dbxml')/Event/Inventory[DeviceID='%s']/ClientVersion/string()" % (DeviceID,), qc)
        cversion.reset()
        for value in cversion:
            print "   is using client version: %s" % (value.asString(),)

    # Remove garnele from the collection add re-add it
    cont.deleteDocument(r"garnele-2011-10-27-16-23-21", uc)
    cont.putDocument(r"garnele-2011-10-27-16-23-21", open('data/xml_content.xml').read(), uc)

    # Query for the used DeviceIDs
    print "\nListing DeviceIDs"
    results = mgr.query("collection('inventory.dbxml')/Event/Inventory/DeviceID/string()", qc)
    results.reset()
    print "Found client inventory data sets for:"
    for value in results:
        print " * %s" % (value.asString(),)

    # Update the DeviceID of garnele to dummy
    print "\nUpdating DeviceID of garnele-2011-10-27-16-23-21 to Dummy"
    mgr.query("replace value of node collection('inventory.dbxml')/Event/Inventory[DeviceID='garnele-2011-10-27-16-23-21']/DeviceID with 'Dummy'", qc)

    # Query for the used DeviceIDs
    print "\nListing DeviceIDs"
    results = mgr.query("collection('inventory.dbxml')/Event/Inventory/DeviceID/string()", qc)
    results.reset()
    print "Found client inventory data sets for:"
    for value in results:
        print " * %s" % (value.asString(),)
