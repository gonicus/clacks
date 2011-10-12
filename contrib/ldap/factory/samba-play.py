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

# Add or remove samba
if not 'SambaUser' in extensions:
    print "Extending!"
    p = f.getObject('SambaUser', u'cn=Playground Tester,ou=people,dc=gonicus,dc=de', mode='extend')
    p.sambaSID = "11111111"
    p.commit()
    exit(0)

else:
    print "Retracting!"
    p = f.getObject('SambaUser', u'cn=Playground Tester,ou=people,dc=gonicus,dc=de')
    p.retract()
    sys.exit(0)




#pprint(p.listProperties())

#p.CtxMaxDisconnectionTime = 223
#p.CtxMaxConnectionTime = 224
#p.CtxWFHomeDir = u'\\Users\\Peter'

#p.acct_isAutoLocked = not p.acct_isAutoLocked

#p.Ctx_flag_defaultPrinter = not p.Ctx_flag_defaultPrinter
#p.Ctx_flag_defaultPrinter = not p.Ctx_flag_defaultPrinter

#print p.Ctx_shadow
#p.Ctx_shadow = 3

#print p.sambaMungedDial

#p.commit()

