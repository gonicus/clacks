import os
import re
import md5
import json
import shutil
import logging
import StringIO
from time import time
from lxml import etree, objectify
from clacks.common import Environment
from clacks.agent.xmldb.interface import XMLDBInterface, XMLDBException
from dbxml import XmlManager, XmlResolver, DBXML_LAZY_DOCS, DBXML_ALLOW_VALIDATION


class dictSchemaResolver(XmlResolver):
    """
    A self made schema resolver which allows DBXML to validate against
    schema that is not physically available, but as string.
    This function receives a dictionary containing the name of the
    schema file as key and the schema-definition as value.
    e.g.:
        res = dictSchemaResolver({'objects': "<?xml versio..."})

    You have to register this resolver to the manager like this.
        resolver = dictSchemaResolver({'..'})
        mgr = XmlManager()
        mgr.registerResolver(resolver)

    """
    schemaData = {}

    def addSchema(self, name, content):
        """
        Adds a new schema to the resolver.

        ======= ===============
        Name    Description
        ======= ===============
        name    The name of the schema file
        content The content (schema-definition)
        ======= ===============

        """
        self.schemaData[name] = content

    def resolveSchema(self, *args):
        """
        Used by the dbxml itself, to resolve schema informations.
        """
        mgr = args[1]
        schemaLocation = args[2]
        if schemaLocation in self.schemaData:
            s = self.schemaData[schemaLocation]
            return(mgr.createMemBufInputStream(s, len(s), True))
        else:

            # No schema found, give another resolver a try.
            return(None)


class DBXml(XMLDBInterface):

    # Logger and clacks environment object
    log = None
    env = None

    # dbxml reslated object
    manager = None
    updateContext = None
    queryContext = None

    # Storage path for dbxml databases
    db_storage_path = None

    # A list of all known collections, namespaces and schemata
    collections = None
    namespaces = None
    schemata = None

    def __init__(self):
        super(DBXml, self).__init__()

        # Enable logging
        self.log = logging.getLogger(__name__)
        self.env = Environment.getInstance()

        self.log.debug("initializing database driver")

        # Create dbxml manager and create schema resolver.
        self.manager = XmlManager()
        self.schemaResolver = dictSchemaResolver()
        self.manager.registerResolver(self.schemaResolver)
        self.queryContext = self.manager.createQueryContext()

        # Check the given storage path - it has to be writeable
        self.db_storage_path = self.env.config.get("dbxml.path", "/var/lib/clacks/database")
        if not os.path.exists(self.db_storage_path):
            raise XMLDBException("storage path '%s' does not exists" % self.db_storage_path)
        if not os.access(self.db_storage_path, os.W_OK):
            raise XMLDBException("storage path '%s' is not writeable" % self.db_storage_path)

        self.log.debug("... done")

        # Open all configured collections
        self.__loadCollections()

        # Get update context
        self.updateContext = self.manager.createUpdateContext()
        self.log.info("dbxml driver successfully initialized with %s database(s)" % (len(self.collections)))

    def __loadCollections(self):
        """
        Pre-load all collections of the configured storage path.
        """

        self.log.debug("going to load existing collections")

        # Search directories containing a config file
        dbs = [n for n in os.listdir(self.db_storage_path) \
                if os.path.exists(os.path.join(self.db_storage_path, n, "config"))]
        self.collections = {}
        self.namespaces = {}
        self.schemata = {}
        self.namespaces['xsi'] = "http://www.w3.org/2001/XMLSchema-instance"

        self.log.debug("found %s potential database folder(s)" % (len(dbs)))
        for db in dbs:

            self.log.debug("processing collection %s" % (db))

            # Read the config file
            data = self.__readConfig(db)
            dfile = os.path.join(self.db_storage_path, db, 'data.bdb')

            # Try opening the collection file
            cont = self.manager.openContainer(str(dfile), DBXML_ALLOW_VALIDATION)
            cont.addAlias(str(data['collection']))
            self.collections[str(data['collection'])] = {
                    'config': data,
                    'container': cont,
                    'path': os.path.join(self.db_storage_path, db),
                    'db_path': dfile}

            # Merge namespace list
            for alias, uri in data['namespaces'].items():
                self.namespaces[alias] = uri

            # Merge list of xml-schema files
            for alias, uri in data['schema'].items():
                self.schemata[alias] = uri

            self.log.debug("successfully read collection %s" % (db))

        # Forward the collected namespaces to the queryContext
        for alias, uri in self.namespaces.items():
            self.queryContext.setNamespace(str(alias), str(uri))
            self.log.debug("setting namespace prefix %s=%s" % (str(alias), str(uri)))

        # Populate known schema files
        for name, schema in self.schemata.items():
            self.schemaResolver.addSchema(str(name), str(schema))
            self.log.debug("setting schema file %s with %s bytes" % (str(name), len(schema)))

    def __readConfig(self, collection):
        """
        Return the collection config file as dictionary.
        """

        # Read the config file
        self.log.debug("reading config for collection '%s'" % collection)
        db = os.path.join(self.db_storage_path, collection)
        cfile = os.path.join(db, 'config')
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
        self.log.debug("updating config for collection '%s'" % collection)
        db = os.path.join(self.db_storage_path, collection)
        cfile = os.path.join(db, 'config')
        f = open(cfile, 'w')
        f.write(json.dumps(data, indent=2))
        f.close()

    def validateSchema (self, collection, name, md5sum=None, schemaString=None):

        # Validate parameters
        if md5sum and schemaString:
            raise XMLDBException("the parameters md5sum and schemaString can not be used together")
        if not md5sum and not schemaString:
            raise XMLDBException("at least one of the parameter md5sum/schemaString has to be given")

        # Get the current database config
        data = self.__readConfig(collection)

        # Check if such a schema exists
        if name not in data['md5_schema']:
            XMLDBException("no such schema definition '%s' found for collection %s!" % (name, collection))

        # Create a checksum when matching against schema-file
        if schemaString:
            md5s = md5.new()
            md5s.update(schemaString)
            md5sum = md5s.hexdigest()

        # Perform matching
        return(md5sum == data['md5_schema'][name])

    def setSchema(self, collection, filename, schema):

        # Create checksum for the schema
        md5sum = md5.new()
        md5sum.update(schema)

        # Read the config file
        data = self.__readConfig(collection)
        if not 'md5_schema' in data:
            data['md5_schema'] = {}

        # Update the schema information
        data['schema'][filename] = schema
        data['md5_schema'][filename] = md5sum.hexdigest()
        self.__saveConfig(collection, data)

        self.log.debug("added/updated schema for collection %s %s (%s bytes)" % (collection, str(filename), len(schema)))
        self.schemaResolver.addSchema(filename, schema)

    def setNamespace(self, collection, alias, namespace):
        # Read the config file
        data = self.__readConfig(collection)
        data['namespaces'][alias] = namespace
        self.__saveConfig(collection, data)

        self.log.debug("added namespace prefix for collection %s %s=%s" % (collection, str(alias), str(namespace)))

        # Only load namespace if not done already - duplicted definition causes errors
        if alias not in self.namespaces:
            self.namespaces[alias] = namespace
            self.queryContext.setNamespace(alias, namespace)

    def createCollection(self, name, namespaces, schema):
        # Assemble db target path
        path = os.path.join(self.db_storage_path, name)
        self.log.debug("going to create collection '%s'" % (name))
        if not os.path.exists(path):
            os.makedirs(path)
        else:
            raise XMLDBException("collection '%s' exists" % name)

        # Create a new dbxml collection
        try:

            # Create a new collection config object
            data = {'collection': name, 'namespaces': namespaces, 'schema': {}, 'md5_schema': {}}
            f = open(os.path.join(path, 'config'), 'w')
            f.write(json.dumps(data, indent=2))
            f.close()
            self.log.debug("config for collection '%s' written" % (name))

            # Create the dbxml collection
            cont = self.manager.createContainer(os.path.join(path, "data.bdb"), DBXML_ALLOW_VALIDATION)

            #TODO: Configure index
            idxspec = cont.getIndexSpecification();
            #idxspec.setAutoIndexing(False)
            idxspec.addIndex("", "o:UUID", "node-element-presence-none")
            idxspec.addIndex("", "o:UUID", "node-element-equality-string")
            cont.setIndexSpecification(idxspec, self.updateContext)

            cont.addAlias(str(name))
            cont.sync()

            self.log.debug("database created for collection '%s'" % (name))

            # Add the new collection to the already-known-list.
            self.collections[str(name)] = {
                    'config': data,
                    'container': cont,
                    'path': path,
                    'db_path': os.path.join(path, 'data.bdb')}

            # Only load namespace if not done already - duplicted definition causes errors
            self.log.debug("adding %s namespace definition(s) for collection '%s'" % (len(data['namespaces'].items()), name))
            for alias, namespace in data['namespaces'].items():
                if alias not in self.namespaces:
                    self.namespaces[alias] = namespace
                    self.queryContext.setNamespace(alias, namespace)

            # Add schema information to the database
            for entry in schema:
                self.setSchema(name, entry, schema[entry])

        # Try some cleanup in case of an error
        except Exception as e:
            try:
                shutil.rmtree(path)
            except OSError:
                pass
            raise XMLDBException("failed to create collection '%s': %s" % (name, str(e)))
        self.log.debug("successfully created collection '%s'" % (name))

    def getCollections(self):
        return self.collections.keys()

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

        self.log.debug("successfully dropped collection '%s'" % (name))

    def addDocument(self, collection, name, contents):
        # Check for collection existence
        if not collection in self.collections:
            raise XMLDBException("collection '%s' does not exists" % collection)

        # Normalize the document path and then add it.
        name = os.path.normpath(name)
        if re.match("^\/", name):
            raise XMLDBException("document names cannot begin with a '/'!")

        self.collections[collection]['container'].putDocument(str(name), contents, self.updateContext)
        self.collections[collection]['container'].sync()

        self.log.debug("successfully added document '%s' to collection '%s'" % (name, collection))

    def deleteDocument(self, collection, name):
        # Check for collection existence
        if not collection in self.collections:
            raise XMLDBException("collection '%s' does not exists" % collection)

        # Remove the document
        name = os.path.normpath(name)
        self.collections[collection]['container'].deleteDocument(str(name), self.updateContext)
        self.collections[collection]['container'].sync()

        self.log.debug("successfully removed document '%s' from collection '%s'" % (name, collection))

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
        name = os.path.normpath(name)
        return (name in self.getDocuments(str(collection)))

    def xquery(self, query):
        q = query.encode('utf-8') if isinstance(query, unicode) else query
        t0 = time()
        res = self.manager.query(q, self.queryContext)
        t1 = time()
        ret = []
        for t in res:
            ret.append(t.asString())

        self.log.debug("performed xquery '%s' with %s results in %0.3fs" % (query, len(ret), t1 - t0))

        return ret

    def syncCollection(self, collection):
        if collection in self.collections:
            self.collections[collection]['container'].sync()

    def xquery_dict(self, query, strip_namespaces=False):
        rs = self.xquery(query)
        ret = []
        for entry in rs:
            res = etree.XML(entry)
            ret.append(self.recursive_dict(res, strip_namespaces))
        return ret

    def recursive_dict(self, element, strip_namespaces=False):
        """
        Resursivly creates a dictionary out of the given etree.XML object.
        """
        res = {}
        for item in element:
            tag = re.sub('^\{([^\}]*)\}', '', item.tag) if strip_namespaces else item.tag
            if not  tag in res:
                res[tag] = []
            if len(item):
                res[tag].append(self.recursive_dict(item, strip_namespaces))
            else:
                res[tag].append(item.text)
        return res
