#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pprint import pprint
from json import loads
from gosa.common.components import AMQPServiceProxy
proxy = AMQPServiceProxy('amqps://cajus:tester@amqp.intranet.gonicus.de/org.gosa')

#proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "request_inventory")

#proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "callDBusMethod", "get_runlevel")
#proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "callDBusMethod", "set_runlevel", 2)

#pprint( proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "callDBusMethod", "get_service", "apache2"))
#pprint(proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "callDBusMethod", "get_services"))
pprint(proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "callDBusMethod", "stop", "apache2"))
pprint(proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "callDBusMethod", "start", "apache2"))
#pprint(proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "callDBusMethod", "restart", "apache2"))
#pprint(proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "callDBusMethod", "reload", "apache2"))


