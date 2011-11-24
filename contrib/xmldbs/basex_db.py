from xmldb_interface import XMLDBInt
import BaseXClient
import os
import re


class BaseXException(Exception):
    pass

class BaseX(XMLDBInt):

    session = None
    currentdb = None
    namespaces = None

    def __init__(self, hostname='localhost', port=1984, user='admin', password='admin'):
        self.namespaces = {}
        self.session = BaseXClient.Session(hostname, port, user, password)

    def setNamespace(self, name, path):
        self.namespaces[name] = path

    def openDatabase(self, name):
        try:
            self.session.execute("open %s" % (name))
        except Exception as e:
            raise BaseXException("Database '%s' could not be opened! Error was: %s" % (name, str(e)))
        self.currentdb = name

    def createDatabase(self, name):
        try:
            self.session.execute("create db %s" % (name))
        except Exception as e:
            raise BaseXException("Database '%s' could not be created! Error was: %s" % (name, str(e)))
        self.currentdb = name

    def dropDatabase(self, name):
        try:
            self.session.execute("drop db %s" % (name))
        except Exception as e:
            raise BaseXException("Database '%s' could not be dropped! Error was: %s" % (name, str(e)))

    def getDocuments(self):
        db = self.currentdb
        res = self.session.execute("list %s" % (db)).split("\n")[2:-3:]
        return(map(lambda x: x.split(" ")[0] , res))

    def documentExists(self, name):
        name = self.__normalizeDocPath(name)
        return name in self.getDocuments()

    def __getDatabases(self):
        res = self.session.execute("list").split("\n")[2:-3:]
        return(map(lambda x: x.split(" ")[0] , res))

    def databaseExists(self, name):
        return name in self.__getDatabases()

    def addDocument(self, name, content):
        # Check if such a document already exists
        name = self.__normalizeDocPath(name)
        res = self.session.execute("list %s" % (self.currentdb)).split("\n")
        if self.documentExists(name):
            raise BaseXException("Document %s already exists!" % (name))

        try:
            self.session.add(name, "", content)
        except Exception as e:
            raise BaseXException("Document '%s' could not be added to '%s'! Error was: %s" % (name, self.currentdb,str(e)))

    def deleteDocument(self, name):
        # Check if such a document exists
        name = self.__normalizeDocPath(name)
        name = self.__normalizeDocPath(name)
        res = self.session.execute("list %s" % (self.currentdb)).split("\n")
        if not self.documentExists(name):
            raise BaseXException("Document does not %s exist!" % (name))
        else:
            try:
                self.session.execute("delete %s" % (name,))
            except Exception as e:
                raise BaseXException("Document '%s' could not be deleted from '%s'! Error was: %s" % (name, self.currentdb,str(e)))

    def __normalizeDocPath(self, name):
        return(re.sub("^\/*","", os.path.normpath(name)))

    def xquery(self, query):

        ns = "xquery "
        for name, url in self.namespaces.items():
            ns += "declare namespace %s='%s';\n" % (name, url)
        query = ns + query;
        return(self.session.execute(query))
