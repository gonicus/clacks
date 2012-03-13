# -*- coding: utf-8 -*-
import pkg_resources
from clacks.common.utils import N_
from clacks.common import Environment
from clacks.common.components import Plugin, Command


class XMLDBHandler(Plugin):

    _priority_ = 0

    # Target queue
    _target_ = 'core'

    instance = None
    __driver = None

    def __init__(self):
        env = Environment.getInstance()
        driver = env.config.get("core.xml-driver", default="DBXml")

        # Find driver module from setuptools advertisement
        for entry in pkg_resources.iter_entry_points("xmldb.driver"):
            mod = entry.load()
            if mod.__name__ == driver:
                self.__driver = mod()
                break

        if not self.__driver:
            raise ValueError("there is no xmldb driver '%s' available" % driver)

    @staticmethod
    def get_instance():
        if not XMLDBHandler.instance:
            XMLDBHandler.instance = XMLDBHandler()

        return XMLDBHandler.instance

    @Command(__help__=N_("Create a new XML database collection"))
    def createCollection(self, name, namespaces, schema):
        return self.__driver.createCollection(name, namespaces, schema)

    @Command(__help__=N_("List available XML database collections"))
    def getCollections(self):
        return self.__driver.getCollections()

    @Command(__help__=N_("Verify if the given XML database collection exists"))
    def collectionExists(self, name):
        return self.__driver.collectionExists(name)

    @Command(__help__=N_("Add XML document to the given XML dabase collection"))
    def addDocument(self, collection, name, contents):
        return self.__driver.addDocument(collection, name, contents)

    @Command(__help__=N_("Verify if the given XML document exists in the XML dabase collection"))
    def documentExists(self, collection, name):
        return self.__driver.documentExists(collection, name)

    @Command(__help__=N_("Get XML documents of a collection"))
    def getDocuments(self, collection):
        return self.__driver.getDocuments(collection)

    @Command(__help__=N_("Perform XQuery and return a list of dicts"))
    def xquery_dict(self, query, collection=None, strip_namespaces=False):
        return self.__driver.xquery_dict(query, collection, strip_namespaces)

    @Command(__help__=N_("Perform XQuery"))
    def xquery(self, query, collection=None):
        return self.__driver.xquery(query, collection)

    @Command(__help__=N_("Set the namespace for a collection"))
    def setNamespace(self, collection, alias, namespace):
        return self.__driver.setNamespace(collection, alias, namespace)

    @Command(__help__=N_("Set a schema for a collection"))
    def setSchema(self, collection, filename, content):
        return self.__driver.setSchema(collection, filename, content)

    @Command(__help__=N_("Validate a schema of a collection"))
    def validateSchema(self, collection, name, md5sum=None, schemaString=None):
        return self.__driver.validateSchema(collection, name, md5sum, schemaString)

    @Command(__help__=N_("Remove a collection"))
    def dropCollection(self, name):
        return self.__driver.dropCollection(name)

    @Command(__help__=N_("Remove a document from a collection"))
    def deleteDocument(self, collection, name):
        return self.__driver.deleteDocument(collection, name)

    @Command(__help__=N_("Synchronize collection"))
    def syncCollection(self, collection):
        return self.__driver.syncCollection(collection)

    def shutdown(self):
        self.__driver.shutdown()
