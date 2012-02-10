#!/usr/bin/env python

import time
from pprint import pprint
from lxml import etree
from lxml import objectify
from clacks.agent.xmldb.handler import XMLDBHandler
from StringIO import StringIO

from json import loads, dumps

xmldb = XMLDBHandler.get_instance()
xmldb.setNamespace('objects', 'xs', "http://www.w3.org/2001/XMLSchema")


query = """

let $objs1 := collection('objects')//*[string(node-name(.)) = ("User")]
let $objs2 := collection('objects')//*[string(node-name(.)) = ("SambaDomain")]

return subsequence(
    for $obj1 in $objs1
        return (
            for $obj2 in $objs2
            where  (
                        $obj2/Attributes/sambaDomainName/text() = $obj1/Attributes/sambaDomainName/text()
                   ) and (
                        contains($obj1/Attributes/cn/text(), 'a')
                   )
            order by $obj1/Attributes/cn/text()
            return (
                concat("dn: ", $obj1/DN/text(),
                    $obj1/Attributes/cn/text(),
                    $obj2/Attributes/sambaDomainName/text(),
                    $obj2/Attributes/sambaLockoutDuration/text()
                )
            )
        )
    ,1,5)
"""

start = time.time()
res = xmldb.xquery(query)
print time.time()-start
pprint(res)


query = """

let $objs1 := collection('objects')//*[string(node-name(.)) = ("User")]

for $obj1 in subsequence($objs1, 1, 10)
    return ($obj1/Attributes/cn/text())

"""

start = time.time()
res = xmldb.xquery(query)
print time.time()-start

pprint(res)
