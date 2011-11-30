import os
import re
import json
import shutil
from dbxml import XmlManager, DBXML_LAZY_DOCS
from xmldb_interface import XMLDBInterface, XMLDBException


class DBXml(XMLDBInterface):

    currentdb = None
    manager = None
    updateContext = None
    queryContext = None
    container = None
    db_storage_path = None
    collections = None
    namespaces = None

    def __init__(self):
        #TODO: load me from the env
        db_path = "/tmp/dbs"

        self.manager = XmlManager()
        self.updateContext = self.manager.createUpdateContext()
        self.queryContext = self.manager.createQueryContext()

        # Check the given database storage path it has to be writeable
        self.db_storage_path = db_path
        if not os.path.exists(self.db_storage_path):
            raise XMLDBException("database storage path '%s' does not exists" % self.db_storage_path)
        if not os.access(self.db_storage_path, os.W_OK):
            raise XMLDBException("database storage path '%s' has to be writeable" % self.db_storage_path)

        # Open all configured databases
        self.__loadDatabases()

    def __loadDatabases(self):
        """
        Pre-loads all databases of the configured storage path.
        """

        # Search directories containing a db.config file
        dbs = [n for n in os.listdir(self.db_storage_path) \
                if os.path.exists(os.path.join(self.db_storage_path, n, "db.config"))]
        self.collections = {}
        self.namespaces = {}
        self.namespaces['xsi'] = "http://www.w3.org/2001/XMLSchema-instance"

        for db in dbs:

            # Read the config file
            data = self.__readConfig(db)
            dfile = os.path.join(self.db_storage_path, db, data['collection'])

            # Try opening the collection file
            cont = self.manager.openContainer(dfile)
            self.collections[data['collection']] = {
                    'config': data,
                    'container': cont,
                    'path': os.path.join(self.db_storage_path, db),
                    'db_path': dfile}

            # Merge namespace list
            for alias, uri in data['namespaces'].items():
                self.namespaces[alias] = uri

        # Forward the collected namespaces to the queryContext
        for alias, uri in self.namespaces.items():
            self.queryContext.setNamespace(alias, uri)

    def __readConfig(self, collection):
        """
        Returns the collection config file as dictionary.
        """

        # Read the config file
        db = os.path.join(self.db_storage_path, collection)
        cfile = os.path.join(db, 'db.config')
        try:
            data = json.loads(open(cfile).read())
        except Exception as e:
            raise XMLDBException("failed loading collection configuration '%s': %s" % (cfile, str(e)))
        if not 'collection' in data:
            raise XMLDBException("invalid collection configuration '%s': missing 'collection' tag" % db)
        if not 'namespaces' in data:
            raise XMLDBException("invalid collection configuration '%s': missing namespaces tag" % db)
        return data

    def __saveConfig(self, collection, data):
        """
        Stores 'data' to the collection-config file.
        """
        db = os.path.join(self.db_storage_path, collection)
        cfile = os.path.join(db, 'db.config')
        f = open(cfile, 'w')
        f.write(json.dumps(data, indent=2))
        f.close()

    def setNamespace(self, collection, alias, namespace):
        """
        Sets a new namespace prefix, which can then be used in queries aso.

        =========== ======================
        Key         Value
        =========== ======================
        collection  The collection to set the namespaces for
        alias       The alias of the namespace
        uri         The namespace uri
        =========== ======================
        """

        # Read the config file
        data = self.__readConfig(collection)
        data['namespaces'][alias] = namespace
        self.__saveConfig(collection, data)

        # Only load namespace if not done already - duplicted definition causes errors
        if alias not in self.namespaces:
            self.namespaces[alias] = namespace
            self.queryContext.setNamespace(alias, namespace)

    def createCollection(self, name, namespaces, schema):
        """
        Creates a new collection

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the collection to create
        =========== ======================
        """

        # Assemble db target path
        path = os.path.join(self.db_storage_path, name)
        if not os.path.exists(path):
            os.makedirs(path)
        else:
            raise XMLDBException("collection '%s' exists" % name)

        # Create a new dbxml collection
        try:

            # Create a new collection config object
            data = {'collection': name, 'namespaces': namespaces, 'schema': schema}
            f = open(os.path.join(path, 'db.config'), 'w')
            f.write(json.dumps(data, indent=2))
            f.close()

            # Create the dbxml collection
            cont = self.manager.createContainer(os.path.join(path, name))#, DBXML_ALLOW_VALIDATION)
            cont.sync()

            # Add the new database to the already-known-list.
            self.collections[name] = {
                    'config': data,
                    'container': cont,
                    'path': path,
                    'db_path': os.path.join(path, name)}

        # Try some cleanup in case of an error
        except Exception as e:
            try:
                shutil.rmtree(path)
            except:
                pass
            raise XMLDBException("failed to create collection '%s': %s" % (name, str(e)))

    def collectionExists(self, name):
        """
        Check whether a given databse exists

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the collection to check for.
        =========== ======================
        """
        return name in self.collections

    def dropCollection(self, name):
        """
        Drops a given collection

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the collection to drop
        =========== ======================
        """

        if not name in self.collections:
            raise XMLDBException("collection '%s' does not exists!" % name)

        # Close the database container
        self.collections[name]['container'].sync()
        del(self.collections[name]['container'])
        self.manager.removeContainer(self.collections[name]['db_path'])

        # Remove the database directory.
        shutil.rmtree(self.collections[name]['path'])
        del(self.collections[name])

    def addDocument(self, collection, docname, content):
        """
        Adds a new document to the currently opened collection.

        =========== ======================
        Key         Value
        =========== ======================
        collection  The name of the collection to add the document to.
        docname     The name of the document to add
        content     The xml content of the document as string
        =========== ======================
        """

        # Check for collection existence
        if not collection in self.collections:
            raise XMLDBException("collection '%s' does not exists" % collection)

        # Normalize the document path and then add it.
        docname = self.__normalizeDocPath(docname)
        self.collections[collection]['container'].putDocument(docname, content, self.updateContext)
        self.collections[collection]['container'].sync()

    def deleteDocument(self, collection, docname):
        """
        Deletes a document from the currently opened collection.

        =========== ======================
        Key         Value
        =========== ======================
        collection      The name of the database to remove from.
        docname     The name of the document to delete
        =========== ======================
        """

        # Check for collection existence
        if not collection in self.collections:
            raise XMLDBException("collection '%s' does not exists" % collection)

        # Remove the document
        docname = self.__normalizeDocPath(docname)
        self.collections[collection]['container'].deleteDocument(docname, self.updateContext)
        self.collections[collection]['container'].sync()

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

    def xquery(self, collections, query):
        """
        Starts a x-query on an opened collection.
        Returns an iterable result set.

        =========== ======================
        Key         Value
        =========== ======================
        collections A list of databases included in this query
        query       The query to execute.
        =========== ======================
        """

        # Prepare collection part for queries.
        dbpaths = []
        for collection in collections:
            dbpaths.append("collection('dbxml:///%s')" % self.collections[collection]['db_path'])

        # Combine collection-part and query-part
        q = "(" + "|".join(dbpaths) + ")" + query

        # Query and fetch all results
        res = self.manager.query(q, self.queryContext)
        ret = []
        for t in res:
            ret.append(t.asString())
        return ret

    def __normalizeDocPath(self, name):
        return(re.sub("^\/*","", os.path.normpath(name)))

