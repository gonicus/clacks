# -*- coding: utf-8 -*- #

import dbxml
import random
import string
import time

mgr = dbxml.XmlManager(dbxml.DBXML_ALLOW_EXTERNAL_ACCESS)
uc = mgr.createUpdateContext()
qc = mgr.createQueryContext()

mgr.reindexContainer("phone4.dbxml", uc)
cont = mgr.openContainer("phone4.dbxml")


start = time.time()
res = mgr.query("collection('phone4.dbxml')//name()", qc)
print time.time() - start


start = time.time()
res = mgr.query("collection('phone4.dbxml')//name()", qc)
print time.time() - start

print "done"
