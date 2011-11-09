#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gosa.common.components import AMQPEventConsumer
from lxml import etree


class InventoryCosumer(object):
    """
    Consumer for inventory events emitted from clients.
    """

    def process(self, data):
        print "Ja", type(data)




c = InventoryCosumer()



# Create event consumer
consumer = AMQPEventConsumer("amqps://amqp:secret@amqp.intranet.gonicus.de:5671/org.gosa",
            xquery="""
                declare namespace f='http://www.gonicus.de/Events';
                let $e := ./f:Event
                return $e/f:Inventory
            """,
            callback=c.process)

# Main loop, process threads
try:
    while True:
        consumer.join()


except KeyboardInterrupt:
    del consumer
    exit(0)
