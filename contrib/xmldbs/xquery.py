#!/usr/bin/env python
# -*- coding: utf-8 -*-
from lxml import etree, objectify
from gosa.agent.xmldb import XMLDBHandler

def print_res(res):
    for r in res:
        print(etree.tostring(objectify.fromstring(r), pretty_print=True))


db = XMLDBHandler.get_instance()

#res = db.xquery("collection('objects')/GenericUser[Attributes/uid/string()='cajus']")
res = db.xquery("collection('objects')/o:GenericUser")
print_res(res)


#<GenericUser xmlns="http://www.gonicus.de/Objects" xmlns:ns_1="http://www.w3.org/2001/XMLSchema-instance" ns_1:schemaLocation="http://www.gonicus.de/Objects objects.xsd">
#  <Type>GenericUser</Type>
#  <UUID>0944c774-ed95-102f-8230-812492b1b75c</UUID>
#  <DN>cn=Roland Rueckert,ou=people,ou=snoovel.com,ou=Mail-Dom&#228;nen,dc=gonicus,dc=de</DN>
#  <LastChanged>2011-06-29T09:08:25</LastChanged>
#  <Extensions>
#    <Extension/>
#  </Extensions>
#  <Attributes>
#    <cn>Roland Rueckert</cn>
#    <givenName>Roland</givenName>
#    <isLocked>false</isLocked>
#    <mail>snoovel.roland@snoovel.com</mail>
#    <passwordMethod>crypt</passwordMethod>
#    <sn>Rueckert</sn>
#    <uid>snoovel.roland</uid>
#    <userPassword>{crypt}b9.yM3lkl4RXA</userPassword>
#  </Attributes>
#</GenericUser>

exit(0)

uuid = "d91fe2d7-f350-443c-b2c2-afed3ac6bbb4"
res = db.xquery("collection('inventory')/gosa:Inventory[gosa:ClientUUID/string()='%s']/gosa:Storage[gosa:Type/string()='disk']" % uuid)

print "Query for disk inventory of", uuid
available_disks = {}
for r in res:
    o = objectify.fromstring(r)
    available_disks[o.Name.text] = o.DiskSize.text

print available_disks


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
