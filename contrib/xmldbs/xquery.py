#!/usr/bin/env python
from lxml import etree, objectify
from gosa.agent.xmldb import XMLDBHandler

def print_res(res):
    for r in res:
        print(etree.tostring(objectify.fromstring(r), pretty_print=True))


db = XMLDBHandler.get_instance()
uuid = "d91fe2d7-f350-443c-b2c2-afed3ac6bbb4"
res = db.xquery("collection('inventory')/gosa:Inventory[gosa:ClientUUID/string()='%s']/gosa:Storage[gosa:Type/string()='disk']" % uuid)

print "Query for disk inventory of", uuid
available_disks = {}
for r in res:
    o = objectify.fromstring(r)
    available_disks[o.Name.text] = o.DiskSize.text

print available_disks


print "Generic xquery tests"
print db.xquery('"What is 12*12?", 12*12')
print db.xquery('let $seq := ("one", "two", "three")\nreturn $seq')
print db.xquery('let $seq := ("one", "two", "three")\nreturn $seq')
print db.xquery('collection("inventory")//gosa:Type[contains(., "disk")]')
res = db.xquery("""xquery version '1.0';
<Results>
{
  let $doc := collection('inventory')
  for $x in $doc//gosa:Storage
  where $x/gosa:Name[contains(., 'sda')] and $x/gosa:Type = 'disk'
  order by $x/gosa:Name
  return
    <Result>
      {$x/gosa:Name}
      {$x/gosa:DiskSize}
    </Result>
}
</Results>
""")

print_res(res)
