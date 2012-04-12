import os
import re
import md5
import json
import shutil
import logging
from time import time
from lxml import etree
from clacks.common import Environment
from clacks.agent.xmldb.interface import XMLDBInterface, XMLDBException
from dbxml import XmlManager, XmlResolver, DBXML_LAZY_DOCS, DBXML_ALLOW_VALIDATION, XmlQueryParserError
from threading import Timer, Lock


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

    # Storage path for dbxml databases
    db_storage_path = None

    # A list of all known collections, namespaces and schemata
    collections = None

    # Database locks, used while reindex and compact are in progress
    _db_locks = None

    # Current database statistics with last modifications etc.
    _db_stats = None

    def __init__(self):
        super(DBXml, self).__init__()

        # Enable logging
        self.log = logging.getLogger(__name__)
        self.env = Environment.getInstance()
        cfg = self.env.config

        # Sync, reindex and compact every n modifications
        self.sync_amount = cfg.get("index.sync_threshold", default=500)
        self.reindex_amount = cfg.get("index.reindex_threshold", default=2000)
        self.compact_amount = cfg.get("index.compact_threshold", default=5000)

        # Sync, reindex and compact after n seconds after the last modification
        self.sync_timeout = cfg.get("index.sync_timeout", default=30)
        self.reindex_timeout = cfg.get("index.reindex_timeout", default=300)
        self.compact_timeout = cfg.get("index.compact_timeout", default=600)

        self.log.debug("initializing database driver")

        # Create dbxml manager and create schema resolver.
        self._db_stats = {}
        self._db_locks = {}
        self.sync_timer = {}
        self.reindex_timer = {}
        self.compact_timer = {}
        self.manager = XmlManager()
        self.schemaResolver = dictSchemaResolver()
        self.manager.registerResolver(self.schemaResolver)

        # Pre-Compile regex
        self.find_collections = re.compile(r"collection\(['\"]([^'\"]+)['\"]\)")
        self.ns_strip = re.compile(r"^\{([^\}]*)\}")

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
        self.log.info("dbxml driver successfully initialized with %s database(s)" % (len(self.collections)))

    def shutdown(self):
        for name in self.sync_timer.keys():
            if self.sync_timer[name]:
                self.sync_timer[name].cancel()

        for name in self.reindex_timer.keys():
            if self.reindex_timer[name]:
                self.reindex_timer[name].cancel()

        for name in self.compact_timer.keys():
            if self.compact_timer[name]:
                self.compact_timer[name].cancel()

        for name in self.collections.keys():
            self.syncCollection(name)

    def __loadCollections(self):
        """
        Pre-load all collections of the configured storage path.
        """

        self.log.debug("going to load existing collections")

        # Search directories containing a config file
        dbs = [n for n in os.listdir(self.db_storage_path) \
                if os.path.exists(os.path.join(self.db_storage_path, n, "config"))]
        self.collections = {}
        self.log.debug("found %s potential database folder(s)" % (len(dbs)))

        # Open each container
        for db in dbs:
            self._loadCollection(db)

    def _loadCollection(self, db):
        """
        Loads and initializes a collection.
        """

        self.log.debug("opening collection %s" % (db))

        # Read the config file
        data = self.__readConfig(db)
        dbname = str(data['collection'])
        dfile = os.path.join(self.db_storage_path, db, 'data.bdb')

        # Try opening the collection file
        cont = self.manager.openContainer(str(dfile), DBXML_ALLOW_VALIDATION)
        cont.addAlias(dbname)
        self.collections[str(data['collection'])] = {
                'config': data,
                'container': cont,
                'namespaces': {},
                'schema': {},
                'queryContext': self.manager.createQueryContext(),
                'updateContext': self.manager.createUpdateContext(),
                'path': os.path.join(self.db_storage_path, db),
                'db_path': dfile}

        # Create a database lock, to be able to avoid db access while reindex or compact are in progress
        self._db_locks[dbname] = Lock()

        self._db_stats[dbname] = {}
        self._db_stats[dbname]['mods_since_last_sync'] = 0
        self._db_stats[dbname]['mods_since_last_reindex'] = 0
        self._db_stats[dbname]['mods_since_last_compact'] = 0
        self._db_stats[dbname]['last_mod'] = 0
        self.sync_timer[dbname] = None
        self.reindex_timer[dbname] = None
        self.compact_timer[dbname] = None

        # Merge namespace list
        contData = self.collections[dbname]
        for alias, uri in data['namespaces'].items():
            contData['queryContext'].setNamespace(str(alias), str(uri))
            contData['namespaces'][str(alias)] = str(uri)
            self.log.debug("setting namespace prefix %s=%s for %s" % (str(alias), str(uri), dbname))

        # Merge list of xml-schema files
        for name, schema in data['schema'].items():
            self.schemaResolver.addSchema(str(name), str(schema))
            self.log.debug("setting schema file %s for %s" % (str(name), dbname))

        self.log.debug("successfully read collection %s" % (dbname))

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
        """
        See :class:`clacks.agent.xmldb.interface.XMLDBInterface` for details.
        """

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
        """
        See :class:`clacks.agent.xmldb.interface.XMLDBInterface` for details.
        """

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
        """
        See :class:`clacks.agent.xmldb.interface.XMLDBInterface` for details.
        """
        # Read the config file
        data = self.__readConfig(collection)
        data['namespaces'][alias] = namespace
        self.__saveConfig(collection, data)
        self.collections[collection]['queryContext'].setNamespace(alias, namespace)
        self.log.debug("added namespace prefix for collection %s %s=%s" % (collection, str(alias), str(namespace)))

    def createCollection(self, name, namespaces, schema):
        """
        See :class:`clacks.agent.xmldb.interface.XMLDBInterface` for details.
        """
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
            data = {'collection': name, 'namespaces': {}, 'schema': {}, 'md5_schema': {}}
            f = open(os.path.join(path, 'config'), 'w')
            f.write(json.dumps(data, indent=2))
            f.close()
            self.log.debug("config for collection '%s' written" % (name))

            # Create the dbxml collection and then load it
            cont = self.manager.createContainer(os.path.join(path, "data.bdb"), DBXML_ALLOW_VALIDATION)
            cont.sync()
            del(cont)
            self._loadCollection(name)

            # Add schema information
            for ids, schema in schema.items():
                self.setSchema(name, ids, schema)

            # Add namespaces
            for ids, url in namespaces.items():
                self.setNamespace(name, ids, url)

            self.log.debug("database created for collection '%s'" % (name))

        # Try some cleanup in case of an error
        except Exception as e:
            try:
                shutil.rmtree(path)
            except OSError:
                pass
            raise XMLDBException("failed to create collection '%s': %s" % (name, str(e)))
        self.log.debug("successfully created collection '%s'" % (name))

    def getCollections(self):
        """
        See :class:`clacks.agent.xmldb.interface.XMLDBInterface` for details.
        """
        return self.collections.keys()

    def collectionExists(self, name):
        """
        See :class:`clacks.agent.xmldb.interface.XMLDBInterface` for details.
        """
        return name in self.collections

    def dropCollection(self, name):
        """
        See :class:`clacks.agent.xmldb.interface.XMLDBInterface` for details.
        """
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
        """
        See :class:`clacks.agent.xmldb.interface.XMLDBInterface` for details.
        """

        self._db_locks[str(collection)].acquire()

        # Check for collection existence
        if not collection in self.collections:
            raise XMLDBException("collection '%s' does not exists" % collection)

        # Normalize the document path and then add it.
        name = os.path.normpath(name)
        if re.match(r"^\/", name):
            raise XMLDBException("document names cannot begin with a '/'!")

        uc = self.collections[collection]['updateContext']
        self.collections[collection]['container'].putDocument(str(name), contents, uc)
        self._db_locks[str(collection)].release()
        self._checkCollection(collection)
        self.log.debug("successfully added document '%s' to collection '%s'" % (name, collection))

    def deleteDocument(self, collection, name):
        """
        See :class:`clacks.agent.xmldb.interface.XMLDBInterface` for details.
        """

        self._db_locks[str(collection)].acquire()

        # Check for collection existence
        if not collection in self.collections:
            raise XMLDBException("collection '%s' does not exists" % collection)

        # Remove the document
        name = os.path.normpath(name)
        uc = self.collections[collection]['updateContext']
        self.collections[collection]['container'].deleteDocument(str(name), uc)
        self._db_locks[str(collection)].release()
        self._checkCollection(collection)

        self.log.debug("successfully removed document '%s' from collection '%s'" % (name, collection))

    def getDocuments(self, collection):
        """
        See :class:`clacks.agent.xmldb.interface.XMLDBInterface` for details.
        """
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
        """
        See :class:`clacks.agent.xmldb.interface.XMLDBInterface` for details.
        """
        name = os.path.normpath(name)
        return (name in self.getDocuments(str(collection)))

    def xquery(self, query, collection=None):
        """
        See :class:`clacks.agent.xmldb.interface.XMLDBInterface` for details.
        """
        if not collection:
            matches = self.find_collections.findall(query)

            if len(matches) != 1:
                raise RuntimeError("Cannot find a unique query context")

            collection = matches[0]

        if collection not in self.collections:
            raise XMLDBException("Invalid collection name given '%s'!" % collection)

        self._db_locks[collection].acquire()
        qcontext = self.collections[collection]['queryContext']
        query_str = query.encode('utf-8') if isinstance(query, unicode) else query
        start = time()
        try:
            res = self.manager.query(query_str, qcontext)
        except XmlQueryParserError as e:
            self.log.error("xquery '%s' failed: %s" % (query_str, str(e)))
            self._db_locks[collection].release()
            raise(e)

        end = time()
        ret = []
        for t in res:
            ret.append(t.asString())

        self.log.debug("performed xquery '%s' with %s results in %0.3fs" % (query, len(ret), end - start))
        self._db_locks[collection].release()

        return ret

    def syncCollection(self, collection):
        """
        Synchronizes changes to the database file.
        """
        if collection in self.collections:

            # Acquire lock, to avoid actions during sync
            self._db_locks[str(collection)].acquire()

            # Time measurement
            start = time()

            # Reset action counters for this collection
            if collection in self._db_stats:
                self._db_stats[collection]['mods_since_last_sync'] = 0

            # Stop potentially timed jobs.
            if self.sync_timer[collection]:
                self.sync_timer[collection].cancel()

            # Start synchronization
            self.collections[collection]['container'].sync()
            self.log.debug("container '%s' was synced in '%s' seconds" % (collection, time() - start))

            # Release locka again
            self._db_locks[str(collection)].release()

    def reindexCollection(self, collection):
        """
        Reindex the container.
        """
        if collection in self.collections:

            # Acquire lock, to avoid actions during reindex
            self._db_locks[str(collection)].acquire()
            start = time()

            # Stop potentially timed jobs.
            if self.reindex_timer[collection]:
                self.reindex_timer[collection].cancel()

            # Reset modification counter for the reindex action
            if collection in self._db_stats:
                self._db_stats[collection]['mods_since_last_reindex'] = 0

            # Close the DB (this is necessary) and reindex the container.
            # Afterwards reopen it.
            path = self.collections[collection]['db_path']
            del(self.collections[collection]['container'])
            uc = self.collections[collection]['updateContext']
            self.manager.reindexContainer(path, uc)
            self.collections[collection]['container'] = self.manager.openContainer(path, DBXML_ALLOW_VALIDATION)
            self.collections[collection]['container'].addAlias(str(collection))

            # Release the lock again
            self.log.debug("container '%s' was reindexed in '%s' seconds" % (collection, time() - start))
            self._db_locks[str(collection)].release()

    def compactCollection(self, collection):
        """
        Compacts the container size.
        """
        if collection in self.collections:

            # Acquire lock, to avoid actions during reindex
            self._db_locks[str(collection)].acquire()
            start = time()

            # Stop potentially timed jobs.
            if self.compact_timer[collection]:
                self.compact_timer[collection].cancel()

            # Reset modification counter for the compact action
            if collection in self._db_stats:
                self._db_stats[collection]['mods_since_last_compact'] = 0

            # Close the container and compact it, afterwards reopen it.
            path = self.collections[collection]['db_path']
            del(self.collections[collection]['container'])
            uc = self.collections[collection]['updateContext']
            self.manager.compactContainer(path, uc)
            self.collections[collection]['container'] = self.manager.openContainer(path, DBXML_ALLOW_VALIDATION)
            self.collections[collection]['container'].addAlias(str(collection))

            # Release the lock again
            self.log.debug("container '%s' was compacted in '%s' seconds" % (collection, time() - start))
            self._db_locks[str(collection)].release()

    def xquery_dict(self, query, collection, strip_namespaces=False):
        """
        See :class:`clacks.agent.xmldb.interface.XMLDBInterface` for details.
        """
        rs = self.xquery(query, collection)
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
            tag = self.ns_strip.sub(item.tag) if strip_namespaces else item.tag
            if not  tag in res:
                res[tag] = []
            if len(item):
                res[tag].append(self.recursive_dict(item, strip_namespaces))
            else:
                res[tag].append(item.text)
        return res

    def _checkCollection(self, name):
        """
        This method checks if sync, reindex or compact actions should be startet
        for the given collection.
        It is called whenever a collection is modified.
        """

        # Add collection statistics if not done already
        name = str(name)
        if not name in self._db_stats:
            self._db_stats[name] = {}
            self._db_stats[name]['mods_since_last_sync'] = 0
            self._db_stats[name]['mods_since_last_reindex'] = 0
            self._db_stats[name]['mods_since_last_compact'] = 0
            self._db_stats[name]['last_mod'] = 0
            self.sync_timer[name] = None
            self.reindex_timer[name] = None
            self.compact_timer[name] = None

        # Increase counters
        self._db_stats[name]['mods_since_last_sync'] += 1
        self._db_stats[name]['mods_since_last_reindex'] += 1
        self._db_stats[name]['mods_since_last_compact'] += 1
        self._db_stats[name]['last_mod'] = time()

        # Stop potentially timed sync jobs.
        if self.sync_timer[name]:
            self.sync_timer[name].cancel()
        if self.reindex_timer[name]:
            self.reindex_timer[name].cancel()
        if self.compact_timer[name]:
            self.compact_timer[name].cancel()

        # Check if we've to perform a SYNC immediately or if we've to start a
        # timed sync job.
        if self._db_stats[name]['mods_since_last_sync'] > self.sync_amount:
            self.syncCollection(name)
        else:
            self.sync_timer[name] = Timer(self.sync_timeout, self.syncCollection, [name])
            self.sync_timer[name].start()

        # Check if we've to perform a REINDEX immediately or if we've to start a
        # timed reindex job.
        if self._db_stats[name]['mods_since_last_reindex'] > self.reindex_amount:
            self.reindexCollection(name)
        else:
            self.reindex_timer[name] = Timer(self.reindex_timeout, self.reindexCollection, [name])
            self.reindex_timer[name].start()

        # Check if we've to perform a COMPACT immediately or if we've to start a
        # timed compact job.
        if self._db_stats[name]['mods_since_last_compact'] > self.compact_amount:
            self.compactCollection(name)
        else:
            self.compact_timer[name] = Timer(self.compact_timeout, self.compactCollection, [name])
            self.compact_timer[name].start()

