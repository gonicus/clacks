# -*- coding: utf-8 -*- #
import dbxml
import random
import string
import time
import os
from random import choice
from new2 import get_user


from clacks.agent.xmldb.handler import XMLDBHandler
driver = XMLDBHandler.get_instance()


if driver.collectionExists('new3.dbxml'):
    driver.dropCollection('new3.dbxml')
driver.createCollection('new3.dbxml', {'': 'http://www.gonicus.de/Objects'}, {'new.xsd': open('new.xsd').read()})

print "*" * 80

display = 100
sync = 500
reindex = 500
compact = 500
search = 5000
search_count = 100

cnt = []
res = ""
first = True
for i in range(20):
    entry, dn = get_user()
    start = time.time()
    driver.addDocument('new3.dbxml', dn, "%s" % entry)
    cnt.append(time.time() - start)

    if i % display == 0 and i != 0:
        print "total %s entries added | \t %s ms/each insert" % (i, (sum(cnt) / display) * 1000)
        cnt = []

for item in driver.xquery("collection('new3.dbxml')/*/name()", "new3.dbxml"):
    print item

