#!/usr/bin/env python
# -*- coding: iso-8859-1 -*- #
import time
from pprint import pprint
from clacks.agent.xmldb.handler import XMLDBHandler

from json import loads, dumps

xmldb = XMLDBHandler.get_instance()
xmldb.setNamespace('objects', 'xs', "http://www.w3.org/2001/XMLSchema")


"""
SELECT User.dn, SambaDomain.sambaDomainName
BASE User ONE "ou=people,ou=Technik,dc=gonicus,dc=de"

"""

query = """
declare default element namespace "http://www.gonicus.de/Objects";
let $Base := collection('objects')//*[DN/text()='ou=Technik,dc=gonicus,dc=de']


return $Base/DN

"""


res_t = []
for i in range(1,10):
    start = time.time()
    res = xmldb.xquery(query)
    res_t.append(time.time()-start)

print "*" * 40
print "Query time: "
pprint(res)
print( max(res_t))
print( reduce(lambda x,y: x+y, res_t) / len(res_t))
print( min(res_t))
