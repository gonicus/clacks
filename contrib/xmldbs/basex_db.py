from xmldb_interface import XMLDBInterface
import BaseXClient
import os
import re


class BaseXException(Exception):
    """
    Exception used for BaseX errors
    """
    pass


class BaseX(XMLDBInterface):
    session = None
    currentdb = None
    namespaces = None

    def __init__(self, hostname='localhost', port=1984, user='admin', password='admin'):
        """
        BaseX-Client class that is able to communicate with the server part of the BaseX.

        =========== ======================
        Key         Value
        =========== ======================
        hostname    The name of the host where the BaseXServer component is running on
        port        The port to connect to.
        user        The username to use for the connection
        password    T password
        =========== ======================
        """

        self.namespaces = {}
        self.session = BaseXClient.Session(hostname, port, user, password)

    def setNamespace(self, name, uri):
        """
        Sets a new namespace prefix, which can then be used in queries aso.

        =========== ======================
        Key         Value
        =========== ======================
        name        The abbreviation/short-name of the namespace
        uri         The namespace uri
        =========== ======================
        """
        self.namespaces[name] = uri

    def openCollection(self, name):
        """
        Open the given collection

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the collection to open
        =========== ======================
        """

        if not self.collectionExists(name):
            self.__createCollection(name)
        try:
            self.session.execute("open %s" % (name))
        except Exception as e:
            raise BaseXException("Collection '%s' could not be opened! Error was: %s" % (name, str(e)))
        self.currentdb = name

    def __createCollection(self, name):
        """
        Creates a new collection

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the collection to create
        =========== ======================
        """
        try:
            self.session.execute("create db %s" % (name))
        except Exception as e:
            raise BaseXException("Collection '%s' could not be created! Error was: %s" % (name, str(e)))
        self.currentdb = name

    def dropCollection(self, name):
        """
        Drops a given collection

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the collection to drop
        =========== ======================
        """
        try:
            self.session.execute("drop db %s" % (name))
        except Exception as e:
            raise BaseXException("Collection '%s' could not be dropped! Error was: %s" % (name, str(e)))

    def getDocuments(self):
        """
        Returns a list of all documents of the currently opened databse.
        """
        db = self.currentdb
        res = self.session.execute("list %s" % (db)).split("\n")[2:-3:]
        return(map(lambda x: x.split(" ")[0] , res))

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
        return name in self.getDocuments()

    def __getCollections(self):
        res = self.session.execute("list").split("\n")[2:-3:]
        return(map(lambda x: x.split(" ")[0] , res))

    def collectionExists(self, name):
        """
        Check whether a given databse exists

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the collection to check for.
        =========== ======================
        """
        return name in self.__getCollections()

    def addDocument(self, name, content):
        """
        Adds a new document to the currently opened collection.

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the document to add
        content     The xml content of the document as string
        =========== ======================
        """
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
        """
        Deletes a document from the currently opened collection.

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the document to delete
        =========== ======================
        """
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
        """
        Starts a x-query on an opened collection.
        Returns an iterable result set.

        =========== ======================
        Key         Value
        =========== ======================
        query       The query to execute.
        =========== ======================
        """
        for name, url in self.namespaces.items():
            query = "declare namespace %s='%s';\n" % (name, url) + query
        ret = []
        res = self.session.query(query)
        res.init()
        while res.more():
            ret.append(res.next())
        res.close()
        return ret
