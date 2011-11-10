#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bsddb3.db import *
from dbxml import *

import sys
if __name__ == "__main__":

    containerName = "inventory.dbxml"

    mgr = XmlManager()

    #mgr.removeContainer(containerName)
    if mgr.existsContainer(containerName) != 0:
        print "XML DB existiert bereits!"
        cont = mgr.openContainer(containerName)
    else:
        print "XML DB erstellt!"
        cont = mgr.createContainer(containerName)

    print cont




