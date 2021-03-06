#!/usr/bin/env python
# -*- coding: utf-8 -*-

from clacks.common.components import AMQPServiceProxy
from clacks.common.event import EventMaker
from lxml import etree

# Connect to AMQP bus
proxy = AMQPServiceProxy('amqp://admin:secret@localhost/org.clacks')

# Example of building event without direct strings...
e = EventMaker()
status = e.Event(
    e.PhoneStatus(
        e.CallerId("012345"),
        e.ReceiverId("12343424"),
        e.Status("busy")
    )
)

# ... which in turn needs to be converted to a string
status = etree.tostring(status, pretty_print=True)

# Send it
proxy.sendEvent(status)
