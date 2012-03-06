# -*- coding: utf-8 -*- #

import dbxml
import random
import string
import time
from lxml import objectify, etree
import StringIO


def testdb(name):
    mgr = dbxml.XmlManager(dbxml.DBXML_ALLOW_EXTERNAL_ACCESS)
    uc = mgr.createUpdateContext()
    qc = mgr.createQueryContext()
    cont = mgr.openContainer(name)

    def timeit(query):
        start = time.time()
        res = mgr.query(query, qc)
        size = res.size()
        return "%s\tfound: %s" % (time.time() - start, size)

    base = """
    declare default element namespace 'http://www.gonicus.de/Objects';
    collection('%s')/User/User[DN = 'cn=ZVxmne6 DVAGMyg,ou=gofax,ou=systems,ou=Technik,dc=gonicus,dc=de']
    """ % name

    one = """
    declare default element namespace 'http://www.gonicus.de/Objects';
    collection('%s')/User/User[matches(DN, '^[^,]*,dc=gonicus,dc=de$')]
    """ % name

    one2 = """
    declare default element namespace 'http://www.gonicus.de/Objects';
    collection('%s')/User/User[matches(DN, '^[^,]*,ou=Technik,dc=gonicus,dc=de$')]
    """ % name

    sub = """
    declare default element namespace 'http://www.gonicus.de/Objects';
    collection('%s')/User/User[ends-with(DN, 'dc=gonicus,dc=de')]/Type
    """ % name

    sub2 = """
    declare default element namespace 'http://www.gonicus.de/Objects';
    collection('%s')/User/User[ends-with(DN, 'ou=Technik,dc=gonicus,dc=de')]/Type
    """ % name

    print "Base:                                ", timeit(base)
    print "One 'dc=gonicus,dc=de':              ", timeit(one)
    print "One 'ou=Technik,dc=gonicus,dc=de':   ", timeit(one2)
    print "Sub 'dc=gonicus,dc=de':              ", timeit(sub)
    print "Sub 'ou=Technik,dc=gonicus,dc=de':   ", timeit(sub2)

print "#" * 100
print "1000 Einträge:"
testdb('1000.dbxml')
print
print "#" * 100
print "10000 Einträge:"
testdb('10000.dbxml')
print

print "done"
