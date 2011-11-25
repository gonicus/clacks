from xmldb_interface import XMLDBInt
from dbxml import *

import os
import re


class DBXmlException(Exception):
    pass


class DBXmlResult(object):
    result = None
    def __init__(self, dbxml_res):
        self.result = dbxml_res
        self.result.reset()

    def __iter__(self):
        return self

    def next(self):
        return self.result.next().asString()


class DBXml(XMLDBInt):

    currentdb = None
    manager = None
    updateContext = None
    queryContext = None
    container = None

    def __init__(self):

        self.manager = XmlManager()
        self.updateContext = self.manager.createUpdateContext()
        self.queryContext = self.manager.createQueryContext()

    def setNamespace(self, name, namespace):
        self.queryContext.setNamespace(name, namespace)

    def createDatabase(self, dbname):
        self.container = self.manager.createContainer(dbname)#, DBXML_ALLOW_VALIDATION)
        self.currentdb = dbname

    def openDatabase(self, dbname):
        self.container = self.manager.openContainer(dbname)
        self.currentdb = dbname

    def databaseExists(self, dbname):
        return self.manager.existsContainer(dbname) != 0

    def dropDatabase(self, dbname):
        if dbname == self.currentdb:
            #self.container.close()
            del(self.container)
        return self.manager.removeContainer(dbname)

    def addDocument(self, name, content):
        name = self.__normalizeDocPath(name)
        return self.container.putDocument(name, content, self.updateContext)

    def deleteDocument(self, name):
        name = self.__normalizeDocPath(name)
        return self.container.deleteDocument(name, self.updateContext)

    def getDocuments(self):
        value = []
        res = self.container.getAllDocuments(DBXML_LAZY_DOCS)
        res.reset()
        for entry in res:
            value.append(entry.asDocument().getName())
        return(value)

    def documentExists(self, name):
        name = self.__normalizeDocPath(name)
        return (name in self.getDocuments())


    def xquery(self, query):
        res = self.manager.query(query, self.queryContext)
        return DBXmlResult(res)

    def __normalizeDocPath(self, name):
        return(re.sub("^\/*","", os.path.normpath(name)))

