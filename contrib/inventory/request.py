#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gosa.common.components import AMQPServiceProxy
proxy = AMQPServiceProxy('amqps://cajus:tester@amqp.intranet.gonicus.de/org.gosa')
proxy.clientDispatch("1a0beb7b-1ada-40aa-83b3-9b7ff59d603d", "request_inventory")
