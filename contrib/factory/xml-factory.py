#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dbxml import *
from gosa.agent.objects import GOsaObjectProxy, GOsaObjectFactory
from gosa.agent.objects.index import ObjectIndex, SCOPE_SUB


class dictSchemaResolver(XmlResolver):
    """
    A self made schema resolver which allows DBXML to validate against
    schema that is not physically available, but as string.
    This function receives a dictionary containing the name of the
    schema file as key and the schema-definition as value.
    e.g.:
        res = dictSchemaResolver({'objects': "<?xml versio..."})

    You have to register this resolver to the manager like this.
        mgr = XmlManager()
        mgr.registerResolver(resolver)

    """
    schemaData = None

    def __init__(self, data):
        super(dictSchemaResolver, self).__init__()
        self.schemaData = data

    def resolveSchema(self, transactionC, mgr, schemaLocation, namespace):
        """
        Used by the dbxml itself, to resolve schema informations.
        """
        if schemaLocation in self.schemaData:
            s = self.schemaData[schemaLocation]
            return(mgr.createMemBufInputStream(s, len(s), True))
        else:
            print "Invalid schema file %s" % (schemaLocation)
            return(None)

# Set database info
containerName = r"database.dbxml"
#mgr = XmlManager(DBXML_ALLOW_EXTERNAL_ACCESS)
mgr = XmlManager()
uc = mgr.createUpdateContext()
qc = mgr.createQueryContext()
qc.setNamespace("", "http://www.gonicus.de/Objects")
qc.setNamespace("gosa", "http://www.gonicus.de/Objects")
qc.setNamespace("xsi","http://www.w3.org/2001/XMLSchema-instance")

# Register our own schema resolver
factory = GOsaObjectFactory.getInstance()
schemaResolver = dictSchemaResolver({'objects.xsd': factory.getXMLObjectSchema(True)})
mgr.registerResolver(schemaResolver)

# Create a clean new database/container on startup that allows schema validation
if mgr.existsContainer(containerName):
    mgr.removeContainer(containerName)
cont = mgr.createContainer(containerName, DBXML_ALLOW_VALIDATION, XMLContainer.NodeContainer)
cont.sync()

# Add entries
l = [
    'cn=Rainer Luelsdorf,ou=people,ou=GL,dc=gonicus,dc=de',
    'cn=Lars Scheiter,ou=people,ou=Technik,dc=gonicus,dc=de',
    'uid=FS-1$,ou=winstations,ou=systems,dc=gonicus,dc=de',
    'uid=WS-WINXP02$,ou=winstations,ou=systems,dc=gonicus,dc=de',
    'uid=XP2TEST$,ou=winstations,ou=systems,dc=gonicus,dc=de',
    'cn=Webadmin Desch,ou=people,ou=Webspace,ou=Extern,dc=gonicus,dc=de',
    'cn=GONICUS Webadmin,ou=people,ou=Webspace,ou=Extern,dc=gonicus,dc=de',
    'cn=Konrad Kleine,ou=people,ou=Technik,dc=gonicus,dc=de',
    'uid=INDEPENDENCE$,ou=winstations,ou=systems,dc=gonicus,dc=de',
    'cn=GO Alfresco,ou=people,dc=gonicus,dc=de']

for entry in l:
    try:
        # Get the object by its dn and then add it to the container.
        obj = GOsaObjectProxy(entry)
        cont.putDocument(obj.uuid, obj.asXML(), uc)

        # A sync is required to get changes synced to the filesystem
        cont.sync()
        print "Added: %s" % (entry,)

    except Exception as e:
        print "Failed to add: %s" % (entry,)
        print e

# Query for PosixUsers
results = mgr.query("collection('%s')/GenericUser[Extensions/Extension='PosixUser']/Attributes/cn/string()" % (containerName,), qc)
results.reset()
print "Found users with posix extensions"
for value in results:
    print " * %s" % (value.asString(),)
