# -*- coding: utf-8 -*- #

import dbxml
import random
import string
import time
from lxml import objectify, etree
import StringIO

mgr = dbxml.XmlManager(dbxml.DBXML_ALLOW_EXTERNAL_ACCESS)
uc = mgr.createUpdateContext()
qc = mgr.createQueryContext()


cont = mgr.openContainer("p10000.dbxml")
start = time.time()
res = mgr.query("collection('p10000.dbxml')", qc)
for entry in res:
    print etree.tostring(objectify.parse(StringIO.StringIO(entry.asString())), pretty_print=True)



print "done"
