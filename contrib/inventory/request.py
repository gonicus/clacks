#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gosa.common.components import AMQPServiceProxy
proxy = AMQPServiceProxy('amqps://cajus:tester@amqp.intranet.gonicus.de/org.gosa')
proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "setRunlevel", 2)
