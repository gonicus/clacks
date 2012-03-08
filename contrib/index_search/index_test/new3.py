# -*- coding: utf-8 -*- #
import time
from new2 import get_user
from clacks.agent.xmldb.handler import XMLDBHandler


driver = XMLDBHandler.get_instance()
if driver.collectionExists('new3.dbxml'):
    driver.dropCollection('new3.dbxml')
driver.createCollection('new3.dbxml', {'': 'http://www.gonicus.de/Objects'}, {'new.xsd': open('new.xsd').read()})


cnt = []
first = True
for i in range(10000):
    entry, dn = get_user()
    start = time.time()
    driver.addDocument('new3.dbxml', dn, "%s" % entry)
    cnt.append(time.time() - start)

    if i % 100 == 0:
        print "total %s entries added | \t %s ms/each insert" % (i, (sum(cnt) / 100) * 1000)
        cnt = []

start = time.time()
driver.xquery("collection('new3.dbxml')/*/name()", "new3.dbxml")
print "query took:",  time.time() - start

