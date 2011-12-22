#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import datetime
import sys
import os
from pprint import pprint
from clacks.agent.objects import GOsaObjectFactory


f = GOsaObjectFactory()

## Update
object_type, extensions =  f.identifyObject(u'cn=Playground Tester,ou=people,dc=gonicus,dc=de')

# Add or remove samba
#if not 'SambaUser' in extensions:
#    p = f.getObject('SambaUser', u'cn=Playground Tester,ou=people,dc=gonicus,dc=de', mode='extend')
#    p.sambaSID = "11111111"
#    p.commit()
#    print "Extending!"
#
#else:
#    p = f.getObject('SambaUser', u'cn=Playground Tester,ou=people,dc=gonicus,dc=de')
#    p.retract()
#    print "Retracting!"

p = f.getObject('SambaUser', u'cn=Playground Tester,ou=people,dc=gonicus,dc=de', mode='update')
for entry in p.listProperties():
    print "%30s" % (entry,), getattr(p, entry)

p = f.getObject('SambaUser', u'cn=Playground Tester,ou=people,dc=gonicus,dc=de', mode='update')
p.sambaSID = "1111222"
p.CtxKeyboardLayout = ""
p.sambaDomainName = u"tester"
p.commit()
