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
    collection('%s')/User/User[parent_dn = 'dc=gonicus,dc=de']
    """ % name

    one2 = """
    declare default element namespace 'http://www.gonicus.de/Objects';
    collection('%s')/User/User[parent_dn = 'ou=Technik,dc=gonicus,dc=de']
    """ % name

    sub = """
    declare default element namespace 'http://www.gonicus.de/Objects';
    collection('%s')/User/User['dc=gonicus,dc=de' = parent_bases/base]
    """ % name

    sub2 = """
    declare default element namespace 'http://www.gonicus.de/Objects';
    collection('%s')/User/User['ou=Technik,dc=gonicus,dc=de' = parent_bases/base]
    """ % name




    old_one = """
    declare default element namespace 'http://www.gonicus.de/Objects';
    collection('%s')/User/User[matches(DN, '^[^,]*,dc=gonicus,dc=de$')]
    """ % name

    old_one2 = """
    declare default element namespace 'http://www.gonicus.de/Objects';
    collection('%s')/User/User[matches(DN, '^[^,]*,ou=Technik,dc=gonicus,dc=de$')]
    """ % name

    old_sub = """
    declare default element namespace 'http://www.gonicus.de/Objects';
    collection('%s')/User/User[ends-with(DN, 'dc=gonicus,dc=de')]
    """ % name

    old_sub2 = """
    declare default element namespace 'http://www.gonicus.de/Objects';
    collection('%s')/User/User[ends-with(DN, 'ou=Technik,dc=gonicus,dc=de')]
    """ % name



    print "Base:                                     ", timeit(base)
    print "One      'dc=gonicus,dc=de':              ", timeit(one)
    print "One old  'dc=gonicus,dc=de':              ", timeit(old_one)
    print "--" * 20
    print "One      'ou=Technik,dc=gonicus,dc=de':   ", timeit(one2)
    print "One old  'ou=Technik,dc=gonicus,dc=de':   ", timeit(old_one2)
    print "--" * 20
    print "Sub      'dc=gonicus,dc=de':              ", timeit(sub)
    print "Sub old  'dc=gonicus,dc=de':              ", timeit(old_sub)
    print "--" * 20
    print "Sub      'ou=Technik,dc=gonicus,dc=de':   ", timeit(sub2)
    print "Sub old  'ou=Technik,dc=gonicus,dc=de':   ", timeit(old_sub2)

print "#" * 100
print "1000 Einträge:"
testdb('p1000.dbxml')
print
print "#" * 100
print "10000 Einträge:"
testdb('p10000.dbxml')
print

print "done"
