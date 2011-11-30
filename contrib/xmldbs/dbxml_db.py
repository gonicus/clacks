import os
import re
import json
import shutil
from dbxml import XmlManager, DBXML_LAZY_DOCS
from xmldb_interface import XMLDBInterface, XMLDBException
from gosa.common import Environment


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
        super(DBXml, self).__init__()
        self.env = Environment.getInstance()
        db_path = self.env.config.get("dbxml.path", "/var/lib/gosa/database")

        self.manager = XmlManager()
        self.updateContext = self.manager.createUpdateContext()
        self.queryContext = self.manager.createQueryContext()

        # Check the given storage path - it has to be writeable
        self.db_storage_path = db_path
        if not os.path.exists(self.db_storage_path):
            raise XMLDBException("storage path '%s' does not exists" % self.db_storage_path)
        if not os.access(self.db_storage_path, os.W_OK):
            raise XMLDBException("storage path '%s' is not writeable" % self.db_storage_path)

        # Open all configured collections
        self.__loadCollections()

    def __loadCollections(self):
        """
        Pre-load all collections of the configured storage path.
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
            cont = self.manager.openContainer(str(dfile))
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
            self.queryContext.setNamespace(str(alias), str(uri))

    def __readConfig(self, collection):
        """
        Return the collection config file as dictionary.
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
        # Read the config file
        data = self.__readConfig(collection)
        data['namespaces'][alias] = namespace
        self.__saveConfig(collection, data)

        # Only load namespace if not done already - duplicted definition causes errors
        if alias not in self.namespaces:
            self.namespaces[alias] = namespace
            self.queryContext.setNamespace(alias, namespace)

    def createCollection(self, name, namespaces, schema):
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
            cont.addAlias(str(name))
            cont.sync()

            # Add the new collection to the already-known-list.
            self.collections[name] = {
                    'config': data,
                    'container': cont,
                    'path': path,
                    'db_path': os.path.join(path, name)}

        # Try some cleanup in case of an error
        except Exception as e:
            try:
                shutil.rmtree(path)
            #TODO: specify the exception to catch
            except:
                pass
            raise XMLDBException("failed to create collection '%s': %s" % (name, str(e)))

    def collectionExists(self, name):
        return name in self.collections

    def dropCollection(self, name):
        if not name in self.collections:
            raise XMLDBException("collection '%s' does not exists!" % name)

        # Close the collection container
        self.collections[name]['container'].sync()
        del(self.collections[name]['container'])
        self.manager.removeContainer(str(self.collections[name]['db_path']))

        # Remove the collection directory.
        shutil.rmtree(self.collections[name]['path'])
        del(self.collections[name])

    def addDocument(self, collection, name, contents):
        # Check for collection existence
        if not collection in self.collections:
            raise XMLDBException("collection '%s' does not exists" % collection)

        # Normalize the document path and then add it.
        name = self.__normalizeDocPath(name)
        self.collections[collection]['container'].putDocument(str(name), contents, self.updateContext)
        self.collections[collection]['container'].sync()

    def deleteDocument(self, collection, name):
        # Check for collection existence
        if not collection in self.collections:
            raise XMLDBException("collection '%s' does not exists" % collection)

        # Remove the document
        name = self.__normalizeDocPath(name)
        self.collections[collection]['container'].deleteDocument(str(name), self.updateContext)
        self.collections[collection]['container'].sync()

    def getDocuments(self, collection):
        # Check for collection existence
        if not collection in self.collections:
            raise XMLDBException("collection '%s' does not exists" % collection)
        value = []
        res = self.collections[collection]['container'].getAllDocuments(DBXML_LAZY_DOCS)
        res.reset()
        for entry in res:
            value.append(entry.asDocument().getName())
        return(value)

    def documentExists(self, collection, name):
        name = self.__normalizeDocPath(name)
        return (name in self.getDocuments(str(collection)))

    def xquery(self, query):
        # Prepare collection part for queries.
        #dbpaths = []
        #for collection in collections:
        #    dbpaths.append("collection('dbxml:///%s')" % self.collections[collection]['db_path'])

        # Combine collection-part and query-part
        #q = "(" + "|".join(dbpaths) + ")" + query

        # Query and fetch all results
        q=query
        res = self.manager.query(q, self.queryContext)
        ret = []
        for t in res:
            ret.append(t.asString())
        return ret

    def __normalizeDocPath(self, name):
        return(re.sub("^\/*","", os.path.normpath(name)))

