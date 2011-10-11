#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import datetime
import sys
import os
import pprint
from gosa.agent.objects import GOsaObjectFactory

f = GOsaObjectFactory()
p = f.getObject('SambaUser', u"cn=Playground Tester,ou=people,dc=gonicus,dc=de", mode="update")

#for prop in p.listProperties():
#    print "Attribute %s: %s" % (prop.ljust(40), getattr(p, prop))

p.sambaLogonTime = datetime.datetime.today()
#p.sambaPwdCanChange = datetime.datetime.today()
#p.sambaKickoffTime = datetime.datetime.today()
#p.sambaLogoffTime = datetime.datetime.today()
#p.sambaPwdLastSet = datetime.datetime.today()
#p.sambaBadPasswordTime = datetime.datetime.today()
#p.sambaPwdMustChange = datetime.datetime.today()
#p.sambaBadPasswordCount = 5
p.displayName += 'P'

#p.passwordNotRequired = True
p.serverTrustAccount = not p.serverTrustAccount
p.sambaHomePath = r"\\hallo\welt"
p.sambaHomeDrive = "D:"

#lh = p.sambaLogonHours
#for entry in lh:
#    print("%s: %s" % (entry, lh[entry]))

#lh[0] = (str(int(not(int(lh[0][0]))))  * 24)
#p.sambaLogonHours = lh

#for entry in lh:
#    print("%s: %s" % (entry, lh[entry]))

#print p.sambaMungedDial
p.defaultPrinter = not p.defaultPrinter
p.defaultPrinter = not p.defaultPrinter
p.inheritMode = True
p.shadow = 1
p.CtxWFHomeDir += u'P'
p.commit()

#print p._extends
