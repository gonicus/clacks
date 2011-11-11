#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bsddb3.db import *
from dbxml import *

import sys
if __name__ == "__main__":

    containerName = r"inventory.dbxml"

    mgr = XmlManager()
    #mgr.removeContainer(containerName)

    uc = mgr.createUpdateContext()
    if mgr.existsContainer(containerName) != 0:
        print "XML DB existiert bereits!"
        cont = mgr.openContainer(containerName)
    else:
        print "XML DB erstellt!"
        cont = mgr.createContainer(containerName)
        cont.putDocument(r"garnele-2011-10-27-16-23-21", open('xml_content.xml').read(), uc)
        cont.putDocument(r"independence-2011-10-27-16-19-50", open('xml_content2.xml').read(), uc)

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

        # Query for garneles
        results2 = mgr.query("collection('inventory.dbxml')/Event/Inventory[DeviceID='%s']/ClientVersion/string()" % (value.asString(),), qc)
        results2.reset()
        for value in results2:
            print "   is using client version: %s" % (value.asString(),)

        print

    # # Query for all used 'Memory' tags
    # results = mgr.query("collection('inventory.dbxml')//Memory", qc)
    # results.reset()
    # for value in results:
    #     document = value.asDocument()
    #     print document.getName(), "=", value.asString()


