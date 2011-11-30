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

print
q = "collection('a')/gosa:GenericUser/gosa:Attributes/gosa:uid/text()"
print "Query single collection: " + q
print db.xquery(q)

print
q = "(collection('a')|collection('b'))/gosa:GenericUser/gosa:Attributes/gosa:uid/text()"
print "Query multiple collections: " + q
print db.xquery(q)

db.dropCollection("a")
db.dropCollection("b")

print "done"

