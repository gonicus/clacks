#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import logging
from lxml import etree, objectify
from gosa.agent.xmldb import XMLDBHandler
from gosa.agent.objects import GOsaObjectProxy, GOsaObjectFactory

# ----

def print_res(res):
    for r in res:
        print(etree.tostring(objectify.fromstring(r), pretty_print=True))


def escapeForXQuery(text):
    html_escape_table = {
       "$": "&#36;",
       "{": "&#123;",
       '}': "&#125;",
       "(": "&#40;",
       ')': "&#41;",
       }
    return "".join(html_escape_table.get(c,c) for c in text)

# ----

db = XMLDBHandler.get_instance()

# Create collection if it is not
if db.collectionExists("structure"):
    db.dropCollection("structure")

fac = GOsaObjectFactory.getInstance()
db.createCollection("structure",
            {"s": "http://www.gonicus.de/Structure",
             "xsi": "http://www.w3.org/2001/XMLSchema-instance",
             "xi": "http://www.w3.org/2001/XInclude"},
            {"structure.xsd": open('/home/cajus/clacks/src/agent/src/gosa/agent/data/structure.xsd').read()})

# Node test
# ----> xi:include

doc = """
<s:Node uuid='032e8e9c-ed95-102f-9ffe-812492b1b75c'
        xmlns:ns_1="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:s="http://www.gonicus.de/Structure"
        xmlns:xi="http://www.w3.org/2001/XInclude">
  <s:Node uuid='0327cfda-ed95-102f-9ff9-812492b1b75c'></s:Node>
  <s:Node uuid='07b4b69e-ed95-102f-81bc-812492b1b75c'></s:Node>
  <xi:include href="doc('objects:/03d2183c-ed95-102f-803b-812492b1b75c')"/>
</s:Node>
"""
db.addDocument('structure', 'root', doc)

# Query node include test
res = db.xquery("collection('structure')")
print_res(res)
