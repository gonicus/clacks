#!/usr/bin/env python
# -*- coding: utf-8 -*-
import StringIO
import logging
from lxml import etree, objectify
from pprint import pprint
from gosa.agent.objects import GOsaObjectProxy
from gosa.agent.objects.index import ObjectIndex, SCOPE_SUB

# Do some searching
ie = ObjectIndex()

import pprint


l = [
    'cn=Rainer Luelsdorf,ou=people,ou=GL,dc=gonicus,dc=de',
    'cn=Lars Scheiter,ou=people,ou=Technik,dc=gonicus,dc=de',
    'cn=Susanne Korb,ou=people,ou=Vertrieb,dc=gonicus,dc=de',
    'cn=Cajus Pollmeier,ou=people,ou=Technik,dc=gonicus,dc=de',
    'cn=GONICUS GONICUS,ou=people,dc=gonicus,dc=de',
    'cn=Admin GOforge,ou=people,ou=Administrativa,dc=gonicus,dc=de',
    'cn=Nagios Monitor,ou=people,ou=Technik,dc=gonicus,dc=de',
    'cn=Vertriebs FAX,ou=people,ou=Vertrieb,dc=gonicus,dc=de',
    'cn=Markus Frielinghausen,ou=people,ou=Technik,dc=gonicus,dc=de',
    'cn=Andre Grabowsky,ou=people,ou=Extern,dc=gonicus,dc=de',
    'cn=Fabian Hickert,ou=people,ou=Technik,dc=gonicus,dc=de',
    'cn=Fabian Hickert,ou=people,ou=Technik,dc=gonicus,dc=de',
    'cn=Christian Patsch,ou=people,ou=Consulting,dc=gonicus,dc=de',
    'cn=Christian Patsch,ou=people,ou=Consulting,dc=gonicus,dc=de',
    'cn=Christian Patsch,ou=people,ou=Consulting,dc=gonicus,dc=de',
    'cn=Carsten Sommer,ou=people,ou=Technik,dc=gonicus,dc=de',
    'cn=Simon Fischer,ou=people,ou=Extern,dc=gonicus,dc=de',
    'cn=Projekt Management,ou=people,ou=Vertrieb,dc=gonicus,dc=de',
    'cn=Hans-Peter Zerres,ou=people,ou=Technik,dc=gonicus,dc=de',
    'cn=Stefan Grote,ou=people,ou=Vertrieb,dc=gonicus,dc=de',
    'cn=Karl Postmann,ou=people,dc=gonicus,dc=de',
    'cn=Jan Wischnat,ou=people,ou=Extern,dc=gonicus,dc=de',
    'cn=Sebastian Denz,ou=people,ou=Technik,dc=gonicus,dc=de',
    'cn=Tester Tester,ou=people,dc=gonicus,dc=de',
    'cn=goforgebugs goforgebugs,ou=people,dc=gonicus,dc=de',
    'cn=gometers gometers,ou=people,dc=gonicus,dc=de',
    'cn=Axel Jahn,ou=people,ou=Extern,dc=gonicus,dc=de',
    'cn=Steven Rines,ou=people,ou=Extern,dc=gonicus,dc=de',
    'cn=presenter presenter,ou=people,ou=Extern,dc=gonicus,dc=de',
    'cn=Jan Wenzel,ou=people,ou=Technik,dc=gonicus,dc=de',
    'cn=Gerd Mayr,ou=people,ou=Extern,dc=gonicus,dc=de',
    'cn=Raum Dreiblitz,ou=people,dc=gonicus,dc=de',
    'cn=Hans Wurst,ou=people,ou=Testbed,dc=gonicus,dc=de',
    'cn=Go Bynari,ou=people,dc=gonicus,dc=de',
    'cn=go bynari2,ou=people,dc=gonicus,dc=de',
    'cn=bynari3 go,ou=people,dc=gonicus,dc=de',
    'cn=Michael Leppke,ou=people,ou=Auszubildende,dc=gonicus,dc=de',
    'cn=Stefan Japes,ou=people,ou=Technik,dc=gonicus,dc=de',
    'cn=Server Raum,ou=people,ou=Phones,ou=Technik,dc=gonicus,dc=de',
    'uid=ADMIN-1$,ou=winstations,ou=systems,dc=gonicus,dc=de',
    'uid=FS-1$,ou=winstations,ou=systems,dc=gonicus,dc=de',
    'uid=WS-WINXP02$,ou=winstations,ou=systems,dc=gonicus,dc=de',
    'uid=XP2TEST$,ou=winstations,ou=systems,dc=gonicus,dc=de',
    'cn=Webadmin Desch,ou=people,ou=Webspace,ou=Extern,dc=gonicus,dc=de',
    'cn=GONICUS Webadmin,ou=people,ou=Webspace,ou=Extern,dc=gonicus,dc=de',
    'cn=Konrad Kleine,ou=people,ou=Technik,dc=gonicus,dc=de',
    'uid=INDEPENDENCE$,ou=winstations,ou=systems,dc=gonicus,dc=de',
    'cn=GO Alfresco,ou=people,dc=gonicus,dc=de']



parser = None
for entry in l:
    print entry
    try:
        obj = GOsaObjectProxy(entry)
        xml = obj.asXml()

        # Create parse for objects
        if not parser:
            schema_root = etree.XML(etree.tostring(obj.getXmlObjectSchema(), pretty_print=True))
            schema = etree.XMLSchema(schema_root)
            parser = objectify.makeparser(schema=schema)

        xml = objectify.fromstring(xml, parser)

        print etree.tostring(xml, pretty_print=True)
    except Exception as e:
        print e

    #xml = objectify.fromstring(xml, parser)

