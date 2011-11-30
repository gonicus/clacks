#from basex_db import BaseX
from dbxml_db import DBXml

db = DBXml()
print "Start"
if not db.collectionExists("horsttest.dbxml"):
    print "Create"
    db.createCollection("horsttest.dbxml", {'gosa2': "hallo"}, {})
print "Set namespace"
db.setNamespace("horsttest.dbxml", "gosa", "http://www.gonicus.de/Objects")
print "Drop"
db.dropCollection("horsttest.dbxml")

print "---"
print "Query test"
print "---"
if db.collectionExists("a"):
    db.dropCollection("a")
db.createCollection("a", {'gosa2': "hallo"}, {})
db.setNamespace("a", "gosa", "http://www.gonicus.de/Objects")
db.addDocument("a", "test", open('dummy.xml').read())
db.addDocument("a", "test2", open('dummy2.xml').read())

print "Documents"
print db.getDocuments("a")
print db.deleteDocument("a", "test2")
print db.documentExists("a", "test")
print db.documentExists("a", "testNe")
print db.getDocuments("a")

if db.collectionExists("b"):
    db.dropCollection("b")
db.createCollection("b", {'gosa2': "hallo"}, {})
db.setNamespace("b", "gosa", "http://www.gonicus.de/Objects")
db.addDocument("b", "test", open('dummy2.xml').read())

print "Query something"
print db.xquery(['b'], "/gosa:GenericUser/gosa:Attributes/gosa:uid/text()")
print db.xquery(['a', 'b'], "/gosa:GenericUser/gosa:Attributes/gosa:uid/text()")

db.dropCollection("a")
db.dropCollection("b")

print "done"



import sys
sys.exit(1)

print "Set namespaces"
db.setNamespace("gosa", "http://www.gonicus.de/Objects")
db.setNamespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")

print "Drop collection if exists"
if db.collectionExists('host'):
    print "... exists"
    db.dropCollection('host')

#print "Create collection"
#db.createCollection('host')
print "Open collection"
db.openCollection('host')
print "Add documents"
db.addDocument('/world1', open("dummy.xml").read())
db.addDocument('/world2', open("dummy2.xml").read())
db.addDocument('/a/world2', "<a>/a/world2</a>")
db.addDocument('/b/world2', "<a><b>/b/world2</b></a>")
db.addDocument('//a//b//c//world2', "<a><b><c>/b/world2</c></b></a>")

print "Exists:\t\t", db.documentExists("/a/b/c/world2")
print "Exists:\t\t", db.documentExists("/a/b/c/world")
print "Query: "
for entry in db.xquery("collection('host')/gosa:GenericUser/gosa:Attributes/gosa:uid/text()"):
    print "\t\t", entry
print "Query: "
for entry in db.xquery("collection('host')/gosa:GenericUser[gosa:UUID='03a82842-ed95-102f-8038-812492b1b75c']/gosa:Extensions/gosa:Extension/text()"):
    print "\t\t", entry
print "Query: "
for entry in db.xquery("collection('host')/gosa:GenericUser[gosa:UUID='03a82842-ed95-102f-8038-812492b1b75c']/gosa:Attributes/gosa:uid/text()"):
    print "\t\t", entry

print "Concurrent queries: "
res = db.xquery("collection('host')//gosa:UUID/text()")
for entry in res:
    res2 = db.xquery("collection('host')//gosa:Attributes/gosa:sn/text()")
    print "\t\t", entry
    for entry2 in res2:
        print "\t\t\t", entry2
        res3 = db.xquery("collection('host')//gosa:Extensions/gosa:Extension/text()")
        for entry3 in res3:
            print "\t\t\t\t", entry3


print "DB Exists:\t", db.collectionExists("host")
print "Docs: \t\t", db.getDocuments()
db.deleteDocument("/a/world2")
db.deleteDocument("/world2")
db.deleteDocument("/a/b/c/world2")
db.deleteDocument("/b/world2")
db.dropCollection('host')



