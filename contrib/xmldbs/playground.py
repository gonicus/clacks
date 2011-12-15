#!/usr/bin/env python
from gosa.agent.xmldb import XMLDBHandler


obj_schema = open("objects.xsd").read()


print
print "=" * 20
print "Simple create drop test"
print "=" * 20
db = XMLDBHandler.get_instance()
if not db.collectionExists("horsttest.dbxml"):
    db.createCollection("horsttest.dbxml", {'gosa2': "hallo"}, {})
db.setNamespace("horsttest.dbxml", "gosa", "http://www.gonicus.de/Objects")
db.dropCollection("horsttest.dbxml")
print " ... done"

print
print "=" * 20
print "Document handling"
print "=" * 20
if db.collectionExists("a"):
    db.dropCollection("a")
db.createCollection("a", {'gosa': "http://www.gonicus.de/Objects"}, {'objects.xsd': obj_schema})
db.addDocument("a", "rainer", open('dummy.xml').read())
db.addDocument("a", "hickert", open('dummy2.xml').read())

print "Documents in the collection:".ljust(40, " "), db.getDocuments("a")
print "Document 'rainer' exists:".ljust(40, " "), db.documentExists("a", "rainer")
print "Document 'hickert' exists:".ljust(40, " "), db.documentExists("a", "hickert")
db.deleteDocument("a", "rainer")
print "Removing document 'rainer'".ljust(40, " "), "done"
print "Documents in the collection:".ljust(40, " "), db.getDocuments("a")
print "Documents in the collection:".ljust(40, " "), db.getDocuments("a")

print
print "=" * 20
print "Querying collections"
print "=" * 20
if db.collectionExists("b"):
    db.dropCollection("b")
db.createCollection("b", {'gosa': "http://www.gonicus.de/Objects"}, {'objects.xsd': obj_schema})
db.addDocument("b", "rainer", open('dummy.xml').read())
db.addDocument("b", "hickert", open('dummy2.xml').read())

print
q = "collection('a')/gosa:User/gosa:Attributes/gosa:uid/text()"
print "Query single collection: " + q
print db.xquery(q)

print
q = "(collection('a')|collection('b'))/gosa:User/gosa:Attributes/gosa:uid/text()"
print "Query multiple collections: " + q
print db.xquery(q)

db.dropCollection("a")
db.dropCollection("b")

print
print "=" * 20
print "Query multiple collections with join test"
print "=" * 20

if not db.collectionExists("users"):
    db.createCollection("users", {'gosa': "http://www.gonicus.de/Objects"}, {'objects.xsd': obj_schema})
    db.addDocument("users", "user/hickert", open('dummy2.xml').read())
    db.addDocument("users", "user/rainer", open('dummy.xml').read())

if not db.collectionExists("groups"):
    db.createCollection("groups", {'gosa': "http://www.gonicus.de/Objects"}, {'objects.xsd': obj_schema})
    db.addDocument("groups", "groups", open('dummy3.xml').read())

q = """
<Status>
    {
       for $component in collection("users")/gosa:User
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
    for $component in collection("users")/gosa:User
       return
            let $groups := collection("groups")/gosa:Groups/gosa:Group[gosa:Member=$component/gosa:Attributes/gosa:uid]
            for $group in $groups
            return
                concat("User: ", $component/gosa:Attributes/gosa:uid/string(), " Group: ", $group/gosa:Name/string())

"""
for entry in db.xquery(str(q)):
    print entry

print
print "=" * 20
print "Update collections"
print "=" * 20
print "done"


q = """
insert nodes
    <gosa:Group>
        <gosa:Name>Neue Gruppe</gosa:Name>
        <gosa:Member>hickert</gosa:Member>
        <gosa:Member>rainer</gosa:Member>
    </gosa:Group>
    after
    doc("groups/groups")/gosa:Groups/gosa:Group[gosa:Name/string()='Gruppe Cheffes']
"""

db.xquery(q)
print "Group entry inserted".ljust(40, " ") + "done (Neue Gruppe)"
g = db.xquery("doc('groups/groups')/gosa:Groups/gosa:Group/gosa:Name/string()")
print "Groups available".ljust(40, " ") + ", ".join(g)

q = """
rename node
    doc("groups/groups")/gosa:Groups/gosa:Group[gosa:Name/string()="Neue Gruppe"]/gosa:Name
    as "gosa:Test"
"""

db.xquery(q)
print "Rename node from Name to Test".ljust(40, " ") + "done"
g = db.xquery("doc('groups/groups')/gosa:Groups/gosa:Group/gosa:Name/string()")
print "Groups available".ljust(40, " ") + ", ".join(g)

q = """
rename node
    doc("groups/groups")/gosa:Groups/gosa:Group[gosa:Test/string()="Neue Gruppe"]/gosa:Test
    as "gosa:Name"
"""

db.xquery(q)
print "Rename node to Name again".ljust(40, " ") + "done"

g = db.xquery("doc('groups/groups')/gosa:Groups/gosa:Group/gosa:Name/string()")
print "Groups available".ljust(40, " ") + ", ".join(g)

print "More details on update, rename, replace actions see http://docs.oracle.com/cd/E17276_01/html/intro_xml/modifyingdocuments.html "

db.dropCollection("users")
db.dropCollection("groups")

