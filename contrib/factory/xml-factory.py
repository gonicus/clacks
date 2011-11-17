#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
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


print obj.asXml()

