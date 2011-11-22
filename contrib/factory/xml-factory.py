#!/usr/bin/env python
# -*- coding: utf-8 -*-
import StringIO
import logging
from lxml import etree, objectify
from pprint import pprint
from gosa.agent.objects import GOsaObjectProxy
from gosa.agent.objects.index import ObjectIndex, SCOPE_SUB

# Do some searching
ie = ObjectIndex()

print "*" * 80
print "Receive"
print "*" * 80

obj = GOsaObjectProxy(u"cn=Claudia Mustermann,ou=people,dc=gonicus,dc=de")

print "  Parent DN:", obj.get_parent_dn()
print "  Type:", obj.get_base_type()
print "  Extensions:", ", ".join(e for e, i in obj.get_extension_types().items() if i)
print "  Given name:", obj.givenName
print "  Last name:", obj.sn

print "*" * 80
print "Receive object as xml"
print "*" * 80


print obj.getXmlObjectSchema()


xml = obj.asXml()

schema_root = etree.XML(etree.tostring(obj.getXmlObjectSchema(), pretty_print=True))
#schema_root = etree.XML(open('a').read())
schema = etree.XMLSchema(schema_root)
parser = objectify.makeparser(schema=schema)
xml = objectify.fromstring(xml, parser)
