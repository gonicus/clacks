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
        cont.putDocument(r"Inventory", open('xml_content.xml').read(), uc)

    qc = mgr.createQueryContext()
    qc.setNamespace("", "http://www.gonicus.de/Events")
    qc.setNamespace("gosa", "http://www.gonicus.de/Events")
    qc.setNamespace("xsi","http://www.w3.org/2001/XMLSchema-instance")
    results = mgr.query("collection('inventory.dbxml')/Event/Inventory/DeviceID", qc)
    results.reset()
    for value in results:
        document = value.asDocument()
        print document.getName(), "=", value.asString()

    results = mgr.query("collection('inventory.dbxml')//Memory", qc)
    results.reset()
    for value in results:
        document = value.asDocument()
        print document.getName(), "=", value.asString()


