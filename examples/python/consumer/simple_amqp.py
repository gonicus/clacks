#!/usr/bin/env python
# -*- coding: utf-8 -*-
from clacks.common.components import AMQPServiceProxy

# Create connection to service
proxy = AMQPServiceProxy('amqps://admin:tester@amqp.intranet.gonicus.de/org.clacks')

# List methods
print proxy.getMethods()

# Create samba password hash
print proxy.mksmbhash("secret")
