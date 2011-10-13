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

#p = f.getObject('SambaUser', u'cn=Playground Tester,ou=people,dc=gonicus,dc=de', mode='update')
#for entry in p.listProperties():
#    print entry, getattr(p, entry)

# Add or remove samba
if not 'SambaUser' in extensions:
    p = f.getObject('SambaUser', u'cn=Playground Tester,ou=people,dc=gonicus,dc=de', mode='extend')
    p.sambaSID = "11111111"
    p.commit()
    print "Extending!"

else:
    p = f.getObject('SambaUser', u'cn=Playground Tester,ou=people,dc=gonicus,dc=de')
    p.retract()
    print "Retracting!"
