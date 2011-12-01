#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import StringIO
import logging
from dbxml import *
from lxml import etree, objectify
from gosa.common import Environment
from gosa.common.components import AMQPEventConsumer
from gosa.agent.plugins.inventory.dbxml_mapping import InventoryDBXml
from gosa.agent.plugins.inventory.consumer import *


# Create event consumer
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s (%(levelname)s): %(message)s')
c = InventoryConsumer()
consumer = AMQPEventConsumer("amqps://cajus:tester@amqp.intranet.gonicus.de:5671/org.gosa",
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
