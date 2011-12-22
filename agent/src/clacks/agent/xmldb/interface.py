# -*- codin utf-8 -*-


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

    def getCollections(self):
        """
        Returns a list of all known collections.
        """
        raise NotImplementedError("getCollections")

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

    def xquery_dict(self, query, strip_namespaces=False):
        """
        =================== ======================
        Key                 Value
        =================== ======================
        query               The query to execute.
        strip_namespaces    Strips namespace prefixed from the result.
        =================== ======================

        Executes an xquery statement
            xquery_dict("collection('db/universe/world.xml')")

        Returns a list of dictionaries
        """
        raise NotImplementedErrorError("xquery_dict")

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

    def setSchema(self, collection, filename, content):
        raise NotImplementedErrorError("setSchema")

    def validateSchema (self, collection, name, md5sum=None, schemaString=None):
        """
        This method can be used to check whether a schema has changed or not.

        You can either check if the md5 sum has changed or you can check against
        a given schema definition by using the schemaString parameter.

        ============== ======================
        Key            Value
        ============== ======================
        collection     The collection the schema belongs to
        name           The schema filename you want to match for.
        md5sum         Can be used to match md5 sums directly
        schemaString   Can be used to match against a given schema string.
        ============== ======================
        """
        raise NotImplementedErrorError("validateSchema")

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

    def syncCollection(self, name):
        """
        Forces a sync for the given collection. This may be needed
        if there's document handling like add/remove nodes().

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the collection to sync
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
