# -*- coding: utf-8 -*-


#TODO
print "#TODO - Update interface methods they are no longer up to date"

class XMLDBException(Exception):
    """
    Exception used for DBXml errors
    """
    pass



class XMLDBInterface(object):

    def __init__(self, collection, schema=None):
        if not self.collectionExists(collection):
            self._createCollection(collection, schema)

        self._openCollection(collection)

    def _openCollection(self):
        """
        Opens an existing collection
        """
        raise NotImplementedErrorError("openCollection")

    def _createCollection(self, name):
        """
        Creates a new collection collection.
        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the collection to create
        =========== ======================
        """
        raise NotImplementedError("createCollection")

    def collectionExists(self, name):
        """
        Checks whethter a databse exists or not

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the collection to check for.
        =========== ======================
        """
        raise NotImplementedError("collectionExists")

    def addDocument(self, name, contents):
        """
        Adds a new document to the collection

        addDocument('/path/world.xml', contents)

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the document to add
        content     The xml content of the document as string
        =========== ======================
        """
        raise NotImplementedErrorError("addDocument")

    def documentExists(self, name):
        """
        Checks whethter a document exists or not

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the document to check for.
        =========== ======================
        """
        raise NotImplementedErrorError("documentExists")

    def getDocuments(self):
        """
        Returns a list of all documents attached to the given collection.
        """
        raise NotImplementedErrorError("getDocuments")

    def xquery(self, query):
        """
        =========== ======================
        Key         Value
        =========== ======================
        query       The query to execute.
        =========== ======================

        Executes an xquery statement
            xquery("collection('db/universe/world.xml')")

        Returns an interable result set.
        """
        raise NotImplementedErrorError("xquery")

    def setNamespace(self, abbr, namespace):
        """
        Sets a namespace abbreviation

        =========== ======================
        Key         Value
        =========== ======================
        name        The abbreviation/short-name of the namespace
        uri         The namespace uri
        =========== ======================
        """
        raise NotImplementedErrorError("setNamespace")

    def dropCollection(self, name):
        """
        Drops the given collection

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the collection to drop
        =========== ======================
        """
        raise NotImplementedError("dropCollection")

    def deleteDocument(self, name):
        """
        Removes the given document from the currently openened collection

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the document to delete
        =========== ======================
        """
        raise NotImplementedErrorError("deleteDocument")
