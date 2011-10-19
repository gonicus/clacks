#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from gosa.agent.objects.proxy import GOsaObjectProxy
from gosa.agent.objects.index import ObjectIndex, SCOPE_SUB

# Do some searching
ie = ObjectIndex()

print "*" * 80
print "Search"
print "*" * 80

for entry in ie.search(base=u"dc=gonicus,dc=de", scope=SCOPE_SUB, fltr={'sn': u'Mustermann'}, attrs=['_dn']):
    print entry['_dn']
    obj = GOsaObjectProxy(entry['_dn'])
    print "* Found", obj.dn
    print "  Parent DN:", obj.get_parent_dn()
    print "  Type:", obj.get_base_type()
    print "  Extensions:", ", ".join(e for e, i in obj.get_extension_types().items() if i)
    print "  Given name:", obj.givenName
    print "  Last name:", obj.sn

# Do a modification
if 1 == 1:
    obj = GOsaObjectProxy(u"cn=Klaus Mustermann,ou=people,dc=gonicus,dc=de")
    obj.roomNumber = "19b"
    obj.givenName = u"Günter"
    #obj.notify("Wichtige Nachricht", u"Hallo Günter - alles wird gut!")
    obj.commit()

print "*" * 80
print "Search"
print "*" * 80

for entry in ie.search(base=u"dc=gonicus,dc=de", scope=SCOPE_SUB, fltr={'sn': u'Mustermann'}, attrs=['_dn']):
    print entry['_dn']
    obj = GOsaObjectProxy(entry['_dn'])
    print "* Found", obj.dn
    print "  Parent DN:", obj.get_parent_dn()
    print "  Type:", obj.get_base_type()
    print "  Extensions:", ", ".join(e for e, i in obj.get_extension_types().items() if i)
    print "  Given name:", obj.givenName
    print "  Last name:", obj.sn

# Do a reverse modification
if 1 == 1:
    obj = GOsaObjectProxy(u"cn=Günter Mustermann,ou=people,dc=gonicus,dc=de")
    obj.roomNumber = "31f"
    obj.givenName = u"Klaus"
    obj.commit()
