#!/usr/bin/env python
# -*- coding: iso-8859-1 -*- #
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

#### class Condition(object):
####     attr = None
####     match = None
#### 
####     def __init__(self, attr, match):
####         self.attr = attr
####         self.match = match
#### 
####     def asXQuery(self, xquery):
####         return( "(matches(%s, '%s'))" % (xquery.get_xquery_attribute(self.attr), self.match))
#### 
#### class And(Condition):
####     left = None
####     right = None
####     connector = 'and'
#### 
####     def __init__(self, left, right):
####         self.left = left
####         self.right = right
#### 
####     def asXQuery(self, xquery):
####         return( "(%s %s %s)" % (self.left.asXQuery(xquery), self.connector, self.right.asXQuery(xquery)))
#### 
#### class Or(And):
####     connector = 'or'
#### 
#### class Join(Condition):
####     left = None
####     right = None
####     join_type = None
#### 
####     JOIN_AND = 1
####     JOIN_OR = 2
#### 
####     def __init__(self, left, right, join):
####         self.left = left
####         self.right = right
####         self.join_type = join
#### 
####     def asXQuery(self, xquery):
####         left = xquery.get_xquery_attribute(self.left) if not isinstance(self.left, Condition) else self.left.asXQuery(xquery)
####         right = xquery.get_xquery_attribute(self.right) if not isinstance(self.right, Condition) else self.right.asXQuery(xquery)
####         return( "(%s %s %s)" % (left, '=', right))
#### 
#### class Where(object):
####     condition = None
#### 
####     def __init__(self, condition):
####         self.condition = condition
#### 
####     def asXQuery(self, xquery):
####         return( "where (%s)" % (self.condition.asXQuery(xquery)))
#### 
#### 
#### 
#### class XQuery(object):
#### 
####     oTypes = None
####     order_by_attrs = None
#### 
####     def get_xquery_attribute(self, attr):
#### 
####         if attr not in self.attrMap:
####             tmp = attr.split(".")
####             a_type = tmp[0]
####             a_attr = tmp[1]
####             if a_type not in self.typeMap:
####                 self.typeMap[a_type] = "%s" % ( a_type)
####             self.attrMap[attr] = "$%s/Attributes/%s/text()" % (self.typeMap[a_type], a_attr)
####         return self.attrMap[attr]
#### 
####     def __init__(self, attributes, where=[], order_by_attrs=[]):
####         self.attributes = attributes
####         self.attrMap = {}
####         self.typeMap = {}
####         self.where_statement = where
####         self.order_by_attrs = order_by_attrs
#### 
####         # Initialize attribute mappings
####         for attr in attributes:
####             self.get_xquery_attribute(attr)
#### 
####     def asXQuery(self):
#### 
####         # Create ODer by statement
####         order_by = ""
####         if len(self.order_by_attrs):
####             order_by = "order by " + ", ".join(map(lambda x: self.attrMap[x], self.order_by_attrs))
#### 
####         # Create where statement
####         where = self.where_statement.asXQuery(self)
#### 
####         # Create result statement
####         result_set = "return(concat("+", ".join(map(lambda x: self.attrMap[x], self.attributes))+"))"
#### 
####         # Build up query here by combining let, for, where, oder by and limit
####         first = True
####         last = ""
####         query = ""
####         for a_type in self.typeMap:
####             tmp  = "\nfor $%s in $%ss"  % (a_type, a_type)
####             if first:
####                 first = False
####                 tmp += "\n  "+where
####                 tmp += "\n  "+order_by
####                 tmp += "\n  "+result_set
####                 tmp =  "\n  ".join(tmp.split("\n"))
####             else:
####                 tmp += "\n  ".join(("\nreturn(%s\n)" % last).split("\n"))
####             last = tmp
#### 
####         query = tmp
#### 
####         # Add collection creation
####         for a_type in self.typeMap:
####             query = "let $%ss := collection('objects')//%s\n" % (self.typeMap[a_type], a_type) + query
#### 
####         return(query)
#### 
#### 
#### 
#### c1 = Join('SambaDomain.sambaDomainName', 'User.sambaDomainName', '=')
#### c2 = Condition('User.cn', 'a')
#### c3 = And(c1,c2)
#### w1 = Where(c3)
#### 
#### 
#### q = XQuery(["User.cn", "User.sn", "User.uid", "SambaDomain.sambaLockoutDuration", "SambaDomain.sambaDomainName"], w1, ['User.cn'])
#### query = q.asXQuery()
#### 
#### query = """
#### 
#### (: Collect possible join-values to minimize loops when iterating through the 'for's
#### :)
#### 
#### declare default element namespace "http://www.gonicus.de/Objects";
#### 
#### let $join_values := distinct-values( (collection('objects')//User/Attributes/sambaDomainName,
####                                     collection('objects')//SambaDomain/Attributes/sambaDomainName) )
#### 
#### (: Prepare lists of potential elements :)
#### let $Users := collection('objects')//User[Attributes/sambaDomainName = $join_values]
#### let $SambaDomains := collection('objects')//SambaDomain[Attributes/sambaDomainName = $join_values]
#### 
#### return subsequence(
####     for $User in $Users
####       return(
####         for $SambaDomain in $SambaDomains
####           where ($SambaDomain/Attributes/sambaDomainName = $User/Attributes/sambaDomainName) and matches($User/Attributes/cn/text(), 'a')
####           order by $User/Attributes/cn
####           return(concat($User/Attributes/cn/text(), $User/Attributes/sn/text(), $User/Attributes/uid/text(), $SambaDomain/Attributes/sambaLockoutDuration/text(), $SambaDomain/Attributes/sambaDomainName/text()))
####       )
#### , 5,10)
#### """


query = """
(: Collect possible join-values to minimize loops when iterating through the 'for's
:)

declare default element namespace "http://www.gonicus.de/Objects";

let $join_values := distinct-values( (collection('objects')//User/Attributes/sambaDomainName,
                                    collection('objects')//SambaDomain/Attributes/sambaDomainName) )

(: Prepare lists of potential elements :)
let $Users := collection('objects')//User[Attributes/sambaDomainName = $join_values]
let $SambaDomains := collection('objects')//SambaDomain[Attributes/sambaDomainName = $join_values]

return subsequence(
for $SambaDomain in $SambaDomains, $User in $Users
    where ($SambaDomain/Attributes/sambaDomainName = $User/Attributes/sambaDomainName)
    order by $User/Attributes/cn
    return(
        concat(
            $User/Attributes/sn/text(),
            $User/Attributes/uid/text(),
            $SambaDomain/Attributes/sambaLockoutDuration/text(),
            $SambaDomain/Attributes/sambaDomainName/text()
             )
          )
, 0,100)

"""


res_t = []
for i in range(1,10):
    start = time.time()
    res = xmldb.xquery(query)
    res_t.append(time.time()-start)

print "*" * 40
print "Query time: "
pprint(res_t)
