#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import datetime
import sys
import os
from pprint import pprint
from clacks.agent.objects import ObjectFactory


f = ObjectFactory()

## Update

cn = u"hickert-test4"

object_type, extensions =  f.identifyObject(u'cn=%s,ou=groups,dc=gonicus,dc=de' % (cn,))

print object_type, extensions

p = f.getObject('PosixGroup', u'cn=%s,ou=groups,dc=gonicus,dc=de' % (cn,), mode='update')
for entry in p.listProperties():
    print "%30s" % (entry,), getattr(p, entry)

p.memberUid= [u"hickert"]
p.gidNumber = -1
p.commit()

p = f.getObject('SambaGroup', u'cn=%s,ou=groups,dc=gonicus,dc=de' % (cn,), mode='update')
p.sambaGroupType = 513
p.sambaGroupType = 514
p.sambaDomainName = "WINNT-TEST"
p.commit()

#p = f.getObject('PosixGroup', u'ou=groups,dc=gonicus,dc=de', mode='create')
#p.cn = cn
#p.commit()
#print "created!"


## Add or remove samba
#if not 'PosixUser' in extensions:
#    p = f.getObject('PosixUser', u'cn=Playground Tester,ou=people,dc=gonicus,dc=de', mode='extend')
#    p.homeDirectory = "\home\hickert"
#    p.gidNumber = 231
#    p.commit()
#    print "Extending!"
#
#else:
#    p = f.getObject('PosixUser', u'cn=Playground Tester,ou=people,dc=gonicus,dc=de')
#    p.retract()
#    print "Retracting!"
#
#p = f.getObject('PosixUser', u'cn=Playground Tester,ou=people,dc=gonicus,dc=de', mode='update')
#p.commit()
