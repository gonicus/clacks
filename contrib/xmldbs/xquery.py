#!/usr/bin/env python
# -*- coding: utf-8 -*-
from lxml import etree, objectify
from clacks.agent.xmldb import XMLDBHandler

def print_res(res):
    for r in res:
        print(etree.tostring(objectify.fromstring(r), pretty_print=True))


db = XMLDBHandler.get_instance()

res = db.xquery("collection('objects')/o:User[o:Attributes/o:uid/string()='cajus']")
print "Query for objects:"
print res, "\n"

uuid = "80d51869-58c3-4d39-9a1b-215d45c2b286"
res = db.xquery("collection('inventory')/e:Inventory[e:ClientUUID/string()='%s']/e:Storage[e:Type/string()='disk']" % uuid)

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
print db.xquery('collection("inventory")//e:Type[contains(., "disk")]')
res = db.xquery("""xquery version '1.0';
<table>
    <tr>
      <td>uuid</td>
      <td>Device name</td>
      <td>Disk size</td>
    </tr>
{
  let $doc := collection('inventory')
  for $x in $doc//e:Storage
  where $x/e:Name[contains(., 'sda')] and $x/e:Type = 'disk'
  order by $x/e:Name
  return
    <tr>
      <td>{$x/../e:ClientUUID}</td>
      <td>{$x/e:Name}</td>
      <td>{$x/e:DiskSize}</td>
    </tr>
}
</table>
""")

print_res(res)
