#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import datetime
import sys
import os
from pprint import pprint
from gosa.agent.objects import GOsaObjectFactory


f = GOsaObjectFactory()

## Update
object_type, extensions =  f.identifyObject(u'cn=Playground Tester,ou=people,dc=gonicus,dc=de')

p = f.getObject('PosixUser', u'cn=Playground Tester,ou=people,dc=gonicus,dc=de', mode='update')
for entry in p.listProperties():
    print "%30s" % (entry,), getattr(p, entry)


# Add or remove samba
if not 'PosixUser' in extensions:
    p = f.getObject('PosixUser', u'cn=Playground Tester,ou=people,dc=gonicus,dc=de', mode='extend')
    p.homeDirectory = "\home\hickert"
    p.gidNumber = 231
    p.commit()
    print "Extending!"

else:
    p = f.getObject('PosixUser', u'cn=Playground Tester,ou=people,dc=gonicus,dc=de')
    p.retract()
    print "Retracting!"


#p = f.getObject('PosixUser', u'cn=Playground Tester,ou=people,dc=gonicus,dc=de', mode='update')
#p.shadowLastChange = datetime.datetime.today().date()
#p.shadowExpire = datetime.datetime.today().date()
#p.commit()
