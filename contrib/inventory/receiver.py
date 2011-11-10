#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, mapper, relationship, backref
from gosa.common.components import AMQPEventConsumer
from lxml import etree

from inventory_types import *

engine = create_engine('sqlite:///:memory:', echo=True)
#engine = create_engine('mysql://root:tester@gosa-playground-squeeze/tester', echo=True)
Session = sessionmaker(bind=engine)
session = Session()
Base.metadata.create_all(engine)

slot = Slot()
ed_user = Client()
ed_user.slots.append(slot)
session.add(ed_user)
session.commit()


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


