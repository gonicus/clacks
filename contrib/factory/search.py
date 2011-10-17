#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gosa.agent.objects import GOsaObjectFactory
from gosa.agent.objects.index import ObjectIndex, SCOPE_ONE, SCOPE_BASE, SCOPE_SUB

ie = ObjectIndex()

# Test synchronisation
if 1 == 1:
    print "-"*80 + "\nSync\n" + "-"*80
    ie.sync_index()
    print "-"*80 + "\nSearch\n" + "-"*80

fltr = {}
#fltr = {'uid': '*us'}
#fltr = {'mail': 'stefan.grote@*'}
#fltr = {'_and': {'uid': 'lorenz', 'givenName': u'Cajus', '_or': {'sn': u'ding', 'sn_2': u'dong', '_gt': ['dob', datetime.datetime.now()]}}}
#fltr = {'_and': {'uid': 'lorenz', 'givenName': u'Cajus', '_or': {'_in': {'sn': [u'ding', u'dong']}, '_gt': ['dob', datetime.datetime.now()]}}}

# Deliver a count for a specific base
print "Count:", ie.count(base="dc=gonicus,dc=de", fltr=fltr)
for e in ie.search(base=u"dc=gonicus,dc=de", scope=SCOPE_SUB, fltr=fltr,
        attrs=['sn', 'givenName', 'uid', 'mail', '_dn'], begin=0, end=10):
    print e

print "-"*80 + "\nEvent\n" + "-"*80
f = GOsaObjectFactory.getInstance()
p = f.getObject('GenericUser', u'cn=Klaus Mustermann,ou=people,dc=gonicus,dc=de')
p.mail = ['munter@brechen.de']
p.commit()
