#!/usr/bin/env python

import sys
import time
from pprint import pprint
from lxml import etree
from lxml import objectify
from clacks.agent.xmldb.handler import XMLDBHandler
from StringIO import StringIO

from json import loads, dumps

xmldb = XMLDBHandler.get_instance()
xmldb.setNamespace('objects', 'xs', "http://www.w3.org/2001/XMLSchema")

attrs = ["User.cn", "User.sn", "User.uid", "SambaDomain.sambaLockoutDuration", "SambaDomain.sambaDomainName"]


class Condition(object):
    attr = None
    match = None

    def __init__(self, attr, match):
        self.attr = attr
        self.match = match

    def asXQuery(self):
        return( "(matches(%s, '%s'))" % (self.attr, self.match))

class And(Condition):
    left = None
    right = None
    connector = 'and'

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def asXQuery(self):
        return( "(%s %s %s)" % (self.left.asXQuery(), self.connector, self.right.asXQuery()))

class Or(And):
    connector = 'or'

class Join(Condition):
    left = None
    right = None
    join_type = None

    JOIN_AND = 1
    JOIN_OR = 2

    def __init__(self, left, right, join):
        self.left = left
        self.right = right
        self.join_type = join

    def asXQuery(self):
        left = self.left if not isinstance(self.left, Condition) else self.left.asXQuery()
        right = self.right if not isinstance(self.right, Condition) else self.right.asXQuery()
        return( "(%s %s %s)" % (left, '=', right))

class Where(object):
    condition = None

    def __init__(self, condition):
        self.condition = condition

    def asXQuery(self):
        return( "where (%s)" % (self.condition.asXQuery()))


c1 = Join('SambaDomain.sambaDomainName', 'User.sambaDomainName', '=')
c2 = Condition('User.cn', 'a')

c3 = And(c1,c2)
w1 = Where(c3)

print w1.asXQuery()






sys.exit(0)



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
