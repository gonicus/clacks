#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import datetime
import sys
import os
from pprint import pprint
from clacks.agent.objects import ObjectFactory

f = ObjectFactory()
p = f.getObject('SambaDomain', u'sambaDomainName=FabianSuperDomain,sambaDomainName=GONICUS,dc=gonicus,dc=de', mode='remove')

for entry in p.listProperties():
    print "%30s" % (entry,), getattr(p, entry)

#p.commit()
p.remove();
