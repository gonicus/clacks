from xmldb_interface import XMLDBInterface
from dbxml import *

import os
import re


class DBXmlException(Exception):
    """
    Exception used for DBXml errors
    """
    pass


class DBXml(XMLDBInterface):

    currentdb = None
    manager = None
    updateContext = None
    queryContext = None
    container = None

    def __init__(self):
        """
        DBXml class that is able to communicate database files.
        """
        self.manager = XmlManager()
        self.updateContext = self.manager.createUpdateContext()
        self.queryContext = self.manager.createQueryContext()

    def setNamespace(self, name, namespace):
        """
        Sets a new namespace prefix, which can then be used in queries aso.

        =========== ======================
        Key         Value
        =========== ======================
        name        The abbreviation/short-name of the namespace
        uri         The namespace uri
        =========== ======================
        """
        self.queryContext.setNamespace(name, namespace)

    def createDatabase(self, dbname):
        """
        Creates a new database

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the database to create
        =========== ======================
        """

        self.container = self.manager.createContainer(dbname)#, DBXML_ALLOW_VALIDATION)
        self.currentdb = dbname

    def openDatabase(self, dbname):
        """
        Open the given database

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the database to open
        =========== ======================
        """

        self.container = self.manager.openContainer(dbname)
        self.currentdb = dbname

    def databaseExists(self, dbname):
        """
        Check whether a given databse exists

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the database to check for.
        =========== ======================
        """

        return self.manager.existsContainer(dbname) != 0

    def dropDatabase(self, dbname):
        """
        Drops a given database

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the database to drop
        =========== ======================
        """

        if dbname == self.currentdb:
            #self.container.close()
            del(self.container)
        return self.manager.removeContainer(dbname)

    def addDocument(self, name, content):
        """
        Adds a new document to the currently opened database.

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the document to add
        content     The xml content of the document as string
        =========== ======================
        """

        name = self.__normalizeDocPath(name)
        return self.container.putDocument(name, content, self.updateContext)

    def deleteDocument(self, name):
        """
        Deletes a document from the currently opened database.

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the document to delete
        =========== ======================
        """

        name = self.__normalizeDocPath(name)
        return self.container.deleteDocument(name, self.updateContext)

    def getDocuments(self):
        """
        Returns a list of all documents of the currently opened databse.
        """

        value = []
        res = self.container.getAllDocuments(DBXML_LAZY_DOCS)
        res.reset()
        for entry in res:
            value.append(entry.asDocument().getName())
        return(value)

    def documentExists(self, name):
        """
        Check whether a given document exists in the
        currently opnened databse or not

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the document to check for.
        =========== ======================
        """

        name = self.__normalizeDocPath(name)
        return (name in self.getDocuments())

    def xquery(self, query):
        """
        Starts a x-query on an opened database.
        Returns an iterable result set.

        =========== ======================
        Key         Value
        =========== ======================
        query       The query to execute.
        =========== ======================
        """

        ret = []
        res = self.manager.query(query, self.queryContext)
        for t in res:
            ret.append(t.asString())
        return ret

    def __normalizeDocPath(self, name):
        return(re.sub("^\/*","", os.path.normpath(name)))

