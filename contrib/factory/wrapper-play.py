#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gosa.agent.objects.proxy import GOsaObjectProxy


obj = GOsaObjectProxy(u"cn=Klaus Mustermann,ou=people,dc=gonicus,dc=de")
print obj.givenName, obj.sn
obj.givenName = u"Günter"
print obj.givenName, obj.sn
obj.notify("Wichtige Nachricht", u"Hallo Günter - alles wird gut!")
