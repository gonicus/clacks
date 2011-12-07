#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gosa.agent.objects import GOsaObjectProxy, GOsaObjectFactory
from gosa.agent.objects.index import ObjectIndex, SCOPE_SUB

factory = GOsaObjectFactory.getInstance()

# Get the object by its dn and then add it to the container.
obj = GOsaObjectProxy("cn=Cajus Pollmeier,ou=People,ou=Technik,dc=gonicus,dc=de")
xml = obj.asXml()

print xml
