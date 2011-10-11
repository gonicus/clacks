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

print p.listProperties()

p.CtxMaxDisconnectionTime = 223
p.CtxMaxConnectionTime = 224
p.CtxWFHomeDir = u'\\Users\\Peter'

p.acct_isAutoLocked = not p.acct_isAutoLocked

p.defaultPrinter = not p.defaultPrinter
p.defaultPrinter = not p.defaultPrinter
p.commit()

