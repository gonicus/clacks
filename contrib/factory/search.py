#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import sys
import argparse
from gosa.agent.objects import GOsaObjectFactory
from gosa.agent.objects.index import ObjectIndex, SCOPE_ONE, SCOPE_BASE, SCOPE_SUB

# Define cla parser
parser = argparse.ArgumentParser(description='Search test')
parser.add_argument('query', metavar='QUERY', type=unicode, help='JSON query', default=None, nargs='?')
parser.add_argument('attrs', metavar='ATTRIBUTE', type=str, help='query attributes', nargs="*")
parser.add_argument('--sync', dest='sync', action='store_true', default=False, help='sync index')
parser.add_argument('--base', dest='base', type=unicode, default="dc=gonicus,dc=de", help='the search base')
parser.add_argument('--scope', dest='scope', default="sub", help='the search scope')
parser.add_argument('--offset', dest='offset', type=int, default=None, help='the search scope')
parser.add_argument('--count', dest='count', type=int, default=None, help='the search scope')
args = parser.parse_args()

# Load filter
try:
    if args.query:
        fltr = json.loads(args.query[0])
    else:
        fltr = {}
except:
    print "Error: invalid filter\n"
    print "Examples:"
    print '  {"uid": "*us"}'
    print '  {"mail": "stefan.grote@*"}'
    print '  {"_and": {"uid": "lorenz", "givenName": u"Cajus", "_or": {"_in": {"sn": [u"ding", u"dong"]}}}}'
    exit(1)

# Load scope
scope = None
if args.scope == "sub":
    scope = SCOPE_SUB
if args.scope == "one":
    scope = SCOPE_ONE
if args.scope == "base":
    scope = SCOPE_BASE
if not scope:
    print "Error: invalid scope"
    exit(1)

sys.argv = [sys.argv[0]]
ie = ObjectIndex()

# Test synchronisation
if args.sync:
    print "Please wait - updating index..."
    ie.sync_index()

start = stop = None
if args.offset and args.count:
    start = args.offset
    stop = args.ofset + args.count - 1

for e in ie.search(base=args.base, scope=scope, fltr=fltr, attrs=args.attrs,
        begin=start, end=stop):
    print e
exit(0)


print "\nCount:", ie.count(base="dc=gonicus,dc=de", fltr=fltr)
