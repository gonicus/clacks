#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gosa.common.components import AMQPServiceProxy
proxy = AMQPServiceProxy('amqps://cajus:tester@amqp.intranet.gonicus.de/org.gosa')
proxy.clientDispatch("708a91f1-01d7-4ea1-bf25-e3c09b7d6c3b", "request_inventory")
