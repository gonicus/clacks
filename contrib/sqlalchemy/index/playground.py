# -*- coding: utf-8 -*-
import uuid
import datetime
from gosa.agent.objects.index import ObjectIndex, SCOPE_ONE, SCOPE_BASE, SCOPE_SUB

ie = ObjectIndex()

u1 = str(uuid.uuid4())
ie.insert(u1, dn=u"cn=Cajus Pollmeier,ou=people,ou=Technik,dc=gonicus,dc=de", sn=u"Pollmeier", givenName=u"Cajus", uid="cajus", mail=['cajus@debian.org', 'cajus@naasa.net', 'pollmeier@gonicus.de'], _lastChanged=datetime.datetime.now())
print ie.exists(u1)

#fltr = {}
#fltr = {'uid': '*us'}
fltr = {'mail': 'cajus@*'}
#fltr = {'_and': {'uid': 'lorenz', 'givenName': u'Cajus', '_or': {'sn': u'ding', 'sn_2': u'dong', '_gt': ['dob', datetime.datetime.now()]}}}
#fltr = {'_and': {'uid': 'lorenz', 'givenName': u'Cajus', '_or': {'_in': {'sn': [u'ding', u'dong']}, '_gt': ['dob', datetime.datetime.now()]}}}

# Deliver a count for a specific base
print "Count:", ie.count(base="dc=gonicus,dc=de", fltr=fltr)
for e in ie.search(base="ou=people,ou=Technik,dc=gonicus,dc=de",
        scope=SCOPE_ONE, fltr=fltr, attrs=['sn', 'givenName', 'uid', 'mail', '_dn'], begin=0, end=10):
    print e

#ie.remove(u1)
#print ie.exists(u1)

#ie.refresh()
