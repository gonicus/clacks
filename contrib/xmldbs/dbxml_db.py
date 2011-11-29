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
    databases = None
    namespaces = None

    def __init__(self, db_path):
        """
        DBXml class that is able to communicate collection files.
        """
        self.manager = XmlManager()
        self.updateContext = self.manager.createUpdateContext()
        self.queryContext = self.manager.createQueryContext()

        # Check the given database storage path it has to be writeable
        self.db_storage_path = db_path
        if not os.path.exists(self.db_storage_path):
            raise XMLDBException("Database storage path '%s' does not exists!")
        if not os.access(self.db_storage_path, os.W_OK):
            raise XMLDBException("Database storage path '%s' has to be writeable!")

        # Open all configured databases
        self.databases = {}
        self.namespaces = {}
        self.__loadDatabases()

    def __loadDatabases(self):
        """
        Pre-loads all databases of the configured storage path.
        """

        # Search directories containing a db.config file
        dbs = [n for n in os.listdir(self.db_storage_path) \
                if os.path.exists(os.path.join(self.db_storage_path, n, "db.config"))]
        self.namespaces = {}
        self.namespaces['xsi'] = "http://www.w3.org/2001/XMLSchema-instance"
        for db in dbs:

            # Read the config file
            data = self.__readConfig(db)
            dfile = os.path.join(self.db_storage_path,n,data['db_name'])

            # Try opening the collection file
            cont = self.manager.openContainer(str(dfile))
            self.databases[data['db_name']]['config'] = data
            self.databases[data['db_name']]['container'] = cont

            # Merge namespace list
            for abbr, ns in data['namespaces'].items():
                self.namespaces[str(abbr)] = str(ns)

        # Forward the collected namespaces to the queryContext
        for abbr, ns in self.namespaces.items():
            self.queryContext.setNamespace(abbr, ns)

    def __readConfig(self, db_name):
        """
        Returns the collection config file as dictionary.
        """

        # Read the config file
        db = os.path.join(self.db_storage_path, db_name)
        cfile = os.path.join(db, 'db.config')
        try:
            data = json.loads(open(cfile).read())
        except Exception as e:
            raise XMLDBException("Failed loadind collection config file '%s'! %s" % (cfile, str(e)))
        if not 'db_name' in data:
            raise XMLDBException("Invalid collection config file in '%s', missing tag '%s'!" % (db, 'db_name'))
        if not 'namespaces' in data:
            raise XMLDBException("Invalid collection config file in '%s', missing tag '%s'!" % (db, 'namespaces'))
        return data

    def __saveConfig(self, db_name, data):
        """
        Stores 'data' to the collection-config file.
        """
        db = os.path.join(self.db_storage_path, db_name)
        cfile = os.path.join(db, 'db.config')
        f = open(cfile, 'w')
        f.write(json.dumps(data, indent=2))
        f.close()

    def setNamespace(self, db, name, namespace):
        """
        Sets a new namespace prefix, which can then be used in queries aso.

        =========== ======================
        Key         Value
        =========== ======================
        db          The database to set the namespaces for
        name        The abbreviation/short-name of the namespace
        uri         The namespace uri
        =========== ======================
        """

        # Read the config file
        name = str(name)
        namespace = str(namespace)
        data = self.__readConfig(db)
        data['namespaces'][name] = namespace
        self.__saveConfig(db, data)

        # Only load namespace if not done already - duplicted definition causes errors
        if name not in self.namespaces:
            self.namespaces[name] = namespace
            self.queryContext.setNamespace(name, namespace)

    def createCollection(self, dbname):
        """
        Creates a new collection

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the collection to create
        =========== ======================
        """

        # Assemble db target path
        path = os.path.join(self.db_storage_path, dbname)
        if not os.path.exists(path):
            os.makedirs(path)
        else:
            raise XMLDBException("Database '%s' already exists!" % (dbname,))

        # Create a new dbxml collection
        try:

            # Create a new database config object
            data = {'db_name': dbname, 'namespaces': {}, 'schema': ''}
            f = open(os.path.join(path, 'db.config'), 'w')
            f.write(json.dumps(data, indent=2))
            f.close()

            # Create the dbxml collection
            cont = self.manager.createContainer(os.path.join(path, dbname))#, DBXML_ALLOW_VALIDATION)
            cont.sync()

            self.databases[dbname]['config'] = data
            self.databases[dbname]['container'] = cont

            # Add the new database to the already-known-list.
            self.databases[dbname] = data

        # Try some cleanup in case of an error
        except Exception as e:
            try:
                shutil.rmtree(path)
            except:
                pass
            raise XMLDBException("Failed to create collection '%s'! %s" % (dbname, str(e)))

    def collectionExists(self, dbname):
        """
        Check whether a given databse exists

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the collection to check for.
        =========== ======================
        """

        return self.manager.existsContainer(dbname) != 0

    def dropCollection(self, dbname):
        """
        Drops a given collection

        =========== ======================
        Key         Value
        =========== ======================
        name        The name of the collection to drop
        =========== ======================
        """

        if dbname == self.currentdb:
            #self.container.close()
            del(self.container)
        return self.manager.removeContainer(dbname)

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

        name = self.__normalizeDocPath(name)
        return self.container.putDocument(name, content, self.updateContext)

    def deleteDocument(self, name):
        """
        Deletes a document from the currently opened collection.

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
        Starts a x-query on an opened collection.
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

