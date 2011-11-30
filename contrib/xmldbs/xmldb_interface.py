# -*- coding: utf-8 -*-


class XMLDBException(Exception):
    """
    Exception used for DBXml errors
    """
    pass



class XMLDBInterface(object):

    def __init__(self):
        pass

    def createCollection(self, name, namespaces, schema):
        """
        Creates a new collection collection.
        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the collection to create
        namespaces  Dictionary of namespaces
        schema      List of schema(s) to include
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

    def addDocument(self, collection, name, contents):
        """
        Adds a new document to the collection

        addDocument('/path/world.xml', contents)

        =========== ======================
        Key         Value
        =========== ======================
        collection  The collection this document belongs to
        name        The name of the document to add
        contents    The XML content of the document as string
        =========== ======================
        """
        raise NotImplementedErrorError("addDocument")

    def documentExists(self, collection, name):
        """
        Checks whethter a document exists or not

        =========== ======================
        Key         Value
        =========== ======================
        collection  The collection this document belongs to
        name        The name of the document to check for.
        =========== ======================
        """
        raise NotImplementedErrorError("documentExists")

    def getDocuments(self, collection):
        """
        Returns a list of all documents attached to the given collection.

        =========== ======================
        Key         Value
        =========== ======================
        collection  The collection this document belongs to
        =========== ======================
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

    def setNamespace(self, collection, alias, namespace):

        """
        Sets a namespace abbreviation

        =========== ======================
        Key         Value
        =========== ======================
        collection  What collection keeps that namespace
        alias       The abbreviation/short-name of the namespace
        namespace   The namespace uri
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

    def deleteDocument(self, collection, name):
        """
        Removes the given document from the currently openened collection

        =========== ======================
        Key         Value
        =========== ======================
        collection  The collection where the document is stored
        name        The name of the document to delete
        =========== ======================
        """
        raise NotImplementedErrorError("deleteDocument")
