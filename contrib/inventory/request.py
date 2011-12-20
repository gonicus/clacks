#!/usr/bin/env python
# -*- coding: utf-8 -*-
from json import loads
from gosa.common.components import AMQPServiceProxy
proxy = AMQPServiceProxy('amqps://cajus:tester@amqp.intranet.gonicus.de/org.gosa')
proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "callDBusMethod", "set_runlevel", 2)


# Stop apache service
print "Stop"
print proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "callDBusMethod", "stop", "apache2")
print " .. done"
print "Status: "
print loads(str(proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "callDBusMethod", "get_services")))['apache2']['running']
print "Start"
print proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "callDBusMethod", "start", "apache2")
print " .. done"
print "Status: "
print loads(str(proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "callDBusMethod", "get_services")))['apache2']['running']
