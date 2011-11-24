
from basex_db import BaseXException, BaseX
from dbxml_db import DBXmlException, DBXml

def test_db(db):

    print "=" *60
    print type(db)
    print "=" *60

    db.setNamespace("gosa", "http://www.gonicus.de/Objects")
    db.setNamespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")

    if db.databaseExists('host'):
        db.dropDatabase('host')

    db.createDatabase('host')
    db.openDatabase('host')
    db.addDocument('/world2', open("dummy.xml").read())
    db.addDocument('/a/world2', "<a>/a/world2</a>")
    db.addDocument('/b/world2', "<a><b>/b/world2</b></a>")
    db.addDocument('//a//b//c//world2', "<a><b><c>/b/world2</c></b></a>")

    print "Exists: ", db.documentExists("/a/b/c/world2")
    print "Exists: ", db.documentExists("/a/b/c/world")
    print "Query: ", db.xquery("collection('host')/gosa:GenericUser/gosa:UUID/text()")

    print "DB Exists: ", db.databaseExists("host")
    print "Docs: ", db.getDocuments()
    db.deleteDocument("/a/b/c/world2")
    db.deleteDocument("/a/world2")
    db.deleteDocument("/world2")
    db.deleteDocument("/b/world2")
    db.dropDatabase('host')



b = BaseX()
test_db(b)

x = DBXml()
test_db(x)
