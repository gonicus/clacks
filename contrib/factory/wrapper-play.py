#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from gosa.agent.objects.proxy import GOsaObjectProxy
from gosa.agent.objects.index import ObjectIndex, SCOPE_SUB

ie = ObjectIndex()
for entry in ie.search(base="dc=gonicus,dc=de", scope=SCOPE_SUB, fltr={'sn': u'Mustermann'}, attrs=['_dn']):
    print entry
    obj = GOsaObjectProxy(entry['_dn'])
    print obj.givenName, obj.sn

#obj.givenName = u"Günter"
#print obj.givenName, obj.sn
#obj.notify("Wichtige Nachricht", u"Hallo Günter - alles wird gut!")
#obj.commit()
