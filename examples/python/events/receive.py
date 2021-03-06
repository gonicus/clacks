#!/usr/bin/env python
# -*- coding: utf-8 -*-

from clacks.common.components import AMQPEventConsumer
from lxml import etree

# Event callback
def process(data):
    print(etree.tostring(data, pretty_print=True))

# Create event consumer
consumer = AMQPEventConsumer("amqps://admin:secret@localhost/org.clacks",
            xquery="""
                declare namespace f='http://www.gonicus.de/Events';
                let $e := ./f:Event
                return $e/f:AsteriskNotification
            """,
            callback=process)

# Main loop, process threads
try:
    while True:
        consumer.join()

except KeyboardInterrupt:
    del consumer
    exit(0)
