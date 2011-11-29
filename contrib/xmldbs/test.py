
from basex_db import BaseX
from dbxml_db import DBXml

def test_db(db):

    print "=" *60
    print type(db)
    print "=" *60

    print "Set namespaces"
    db.setNamespace("gosa", "http://www.gonicus.de/Objects")
    db.setNamespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")

    print "Drop database if exists"
    if db.databaseExists('host'):
        print "... exists"
        db.dropDatabase('host')

    print "Create database"
    db.createDatabase('host')
    print "Open database"
    db.openDatabase('host')
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


    print "DB Exists:\t", db.databaseExists("host")
    print "Docs: \t\t", db.getDocuments()
    db.deleteDocument("/a/world2")
    db.deleteDocument("/world2")
    db.deleteDocument("/a/b/c/world2")
    db.deleteDocument("/b/world2")
    db.dropDatabase('host')



b = BaseX()
test_db(b)

x = DBXml()
test_db(x)

