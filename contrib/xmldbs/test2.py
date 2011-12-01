
#from basex_db import BaseX
from dbxml_db import DBXml


obj_schema = open("objects.xsd").read()


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
db.createCollection("a", {'gosa': "http://www.gonicus.de/Objects"}, {'objects.xsd': obj_schema})
db.addDocument("a", "rainer", open('dummy.xml').read())
db.addDocument("a", "hickert", open('dummy2.xml').read())

print "Documents"
print db.getDocuments("a")
print db.deleteDocument("a", "rainer")
print db.documentExists("a", "rainer")
print db.documentExists("a", "hickert")
print db.getDocuments("a")

if db.collectionExists("b"):
    db.dropCollection("b")
db.createCollection("b", {'gosa': "http://www.gonicus.de/Objects"}, {'objects.xsd': obj_schema})
db.addDocument("b", "rainer", open('dummy.xml').read())
db.addDocument("b", "hickert", open('dummy2.xml').read())

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

print "---"
print "Query multiple collections with join test"
print "---"

if db.collectionExists("users"):
    db.dropCollection("users")
db.createCollection("users", {'gosa': "http://www.gonicus.de/Objects"}, {'objects.xsd': obj_schema})
db.addDocument("users", "hickert", open('dummy2.xml').read())
db.addDocument("users", "rainer", open('dummy.xml').read())

if db.collectionExists("groups"):
    db.dropCollection("groups")
db.createCollection("groups", {'gosa': "http://www.gonicus.de/Objects"}, {'objects.xsd': obj_schema})
db.addDocument("groups", "groups", open('dummy3.xml').read())

q = """
<Status>
    {
       for $component in collection("users")/gosa:GenericUser
       return
         <User>
            <Name>{$component/gosa:Attributes/gosa:uid/string()}</Name>
            {
                for $group in collection("groups")/gosa:Groups/gosa:Group[gosa:Member=$component/gosa:Attributes/gosa:uid]
                return
                  <Group>{$group/gosa:Name/string()}</Group>
            }

         </User>
    }
</Status>
"""
print(db.xquery(str(q))[0])

q = """
"Produkt von 12*12",
12*12,
"Ende"
"""
print(db.xquery(str(q)))

q = """
    for $component in collection("users")/gosa:GenericUser
       return
            let $groups := collection("groups")/gosa:Groups/gosa:Group[gosa:Member=$component/gosa:Attributes/gosa:uid]
            for $group in $groups
            return
                concat("User: ", $component/gosa:Attributes/gosa:uid/string(), " Group: ", $group/gosa:Name/string())

"""
for entry in db.xquery(str(q)):
    print entry

db.dropCollection("users")
db.dropCollection("groups")


print "done"

