#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import datetime
import sys
import os
import zope.event
from gosa.agent.objects import GOsaObjectFactory, ObjectQuery


# Register pseudo event handler
def l(event):
    print "%s event catched: %s of %s" % (event.__class__.__name__, event.reason, event.uuid)

zope.event.subscribers.append(l)

# use create, update, remove, move, extend, retract
if len(sys.argv) != 2:
    mode = 'update'
else:
    mode = sys.argv[1]
    del sys.argv[1]

f = GOsaObjectFactory.getInstance()
#for entry in ObjectQuery("dc=gonicus,dc=de", fltr="GenericUser", attrs=['sn', 'givenName', 'uid']):
#    print entry
#
#exit(0)

if mode == "create":
    p = f.getObject('GenericUser', u'ou=people,dc=gonicus,dc=de', mode="create")

if mode in ["update", "move", "remove"]:
    p = f.getObject('GenericUser', u"cn=Klaus Mustermann,ou=people,dc=gonicus,dc=de")

if mode == "extend":
    p = f.getObject('PosixUser', u'cn=Klaus Mustermann,ou=people,dc=gonicus,dc=de', mode="extend")
    p.uidNumber = 4711
    p.gidNumber = 4711
    p.homeDirectory = "/home/cajus"
    p.commit()
    exit(0)

if mode == "retract":
    p = f.getObject('PosixUser', u'cn=Klaus Mustermann,ou=people,dc=gonicus,dc=de')
    p.retract()
    exit(0)

if mode == "remove":
    p.remove()
    exit(0)

if mode == "move":
    p.move("ou=people,ou=Technik,dc=gonicus,dc=de")
    p.move("ou=people,dc=gonicus,dc=de")
    exit(0)

#print "Object type:", type(p)
#print "sn:", p.sn
#print "commonName:", p.commonName
#print "givenName:", p.givenName
#print "userPassword:", p.userPassword
#print "passwordMethod:", p.passwordMethod
#print "dateOfBirth:", p.dateOfBirth
#print "gotoLastSystemLogin:", p.gotoLastSystemLogin
#print "roomNumber:", p.roomNumber
#p.sn = u"Name"
#p.givenName = u"Neuer"
#p.notify(u"This is my title", u"To my amazing message!")
#p.notify(notify_title = u"This is my title", notify_message = u"To my amazing message!")
#p.notify(notify_message = u"To my amazing message!")

#print "Object type:", type(p)
#print "sn:", p.sn
#print "cn:", p.cn


#p.sn = u"Nameneu"
#p.userPassword = u"secret"
#p.givenName = u"Neuer"
#p.notify(u"This is my title", u"To my amazing message!")
#p.notify(notify_title = u"This is my title", notify_message = u"To my amazing message!")
#p.notify(notify_message = u"To my amazing message!")

#print "givenName:", p.givenName
#print "cn:", p.cn
#print "sn:", p.sn
#p.commit()

#print "Object type:", type(p)
#print "sn:", p.sn
#print "cn:", p.cn

p.sn = u"Mustermann"
#p.cn = u"Mustermann"
p.uid = 'mustermann'
p.givenName = u"Klaus"
p.sn = u"Mustermann"
p.userPassword = u"secret"

#del(p.uid)
p.roomNumber = 21
#open('dummy.gif_read', 'w').write(p.jpegPhoto)
p.jpegPhoto =  open('dummy.gif', 'r').read()
#p.gotoLastSystemLogin = datetime.datetime.today()
#p.dateOfBirth = datetime.datetime.today().date()
#p.gender = "M"
p.telephoneNumber = ['123', '333' , '1231']
p.commit()
