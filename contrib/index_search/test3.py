#!/usr/bin/env python

from pprint import pprint
from lxml import etree
from lxml import objectify
from clacks.agent.xmldb.handler import XMLDBHandler
from StringIO import StringIO

from json import loads, dumps

xmldb = XMLDBHandler.get_instance()
xmldb.setNamespace('objects', 'xs', "http://www.w3.org/2001/XMLSchema")


query = """
let $objs := collection('objects')//*[string(node-name(.)) = ("User", "OrganizationalUnit")]
for $obj in $objs
return string(node-name($obj))

"""

res = xmldb.xquery(query)
pprint(res)

try:
    for entry in res:
        print "-" * 20
        pprint(loads(entry))
except Exception as e:
    print entry
    print "Nope!!", e
    raise

print len(res)
