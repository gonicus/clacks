#!/usr/bin/env python
# -*- coding: utf-8 -*-
from lxml import etree, objectify
from gosa.agent.xmldb import XMLDBHandler

def print_res(res):
    for r in res:
        print(etree.tostring(objectify.fromstring(r), pretty_print=True))


db = XMLDBHandler.get_instance()

#res = db.xquery("collection('objects')//node()[o:DN='ou=people,dc=gonicus,dc=de']/o:Attributes[last()]")
res = db.xquery("collection('objects')")
print_res(res)
exit(0)

res = db.xquery("collection('objects')/o:User[o:Attributes/o:uid/string()='cajus']")
print "Query for objects:"
print res, "\n"

uuid = "d91fe2d7-f350-443c-b2c2-afed3ac6bbb4"
res = db.xquery("collection('inventory')/gosa:Inventory[gosa:ClientUUID/string()='%s']/gosa:Storage[gosa:Type/string()='disk']" % uuid)

print "Query for disk inventory of", uuid
available_disks = {}
for r in res:
    o = objectify.fromstring(r)
    available_disks[o.Name.text] = o.DiskSize.text

print available_disks, "\n"


print "Generic xquery tests"
print db.xquery(u'"What is über 12*12?", 12*12')
print db.xquery('let $seq := ("one", "two", "three")\nreturn $seq')
print db.xquery('let $seq := ("one", "two", "three")\nreturn $seq')
print db.xquery('collection("inventory")//gosa:Type[contains(., "disk")]')
res = db.xquery("""xquery version '1.0';
<table>
    <tr>
      <td>uuid</td>
      <td>Device name</td>
      <td>Disk size</td>
    </tr>
{
  let $doc := collection('inventory')
  for $x in $doc//gosa:Storage
  where $x/gosa:Name[contains(., 'sda')] and $x/gosa:Type = 'disk'
  order by $x/gosa:Name
  return
    <tr>
      <td>{$x/../gosa:ClientUUID}</td>
      <td>{$x/gosa:Name}</td>
      <td>{$x/gosa:DiskSize}</td>
    </tr>
}
</table>
""")

print_res(res)
