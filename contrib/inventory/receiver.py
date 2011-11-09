#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gosa.common.components import AMQPEventConsumer
from lxml import etree

# Event callback
def process(data):
    print type(etree.tostring(data, pretty_print=True))

# Create event consumer
consumer = AMQPEventConsumer("amqps://amqp:secret@amqp.intranet.gonicus.de:5671/org.gosa",
            xquery="""
                declare namespace f='http://www.gonicus.de/Events';
                let $e := ./f:Event
                return $e/f:Inventory
            """,
            callback=process)

# Main loop, process threads
try:
    while True:
        consumer.join()


except KeyboardInterrupt:
    del consumer
    exit(0)
