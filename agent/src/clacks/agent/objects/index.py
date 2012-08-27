# -*- coding: utf-8 -*-
"""
Object Index
============

The Object Index is the search engine in clacks. It keeps track about
all defined object types and can find references to it inside of its
local index database

----
"""
import logging
import zope.event
import datetime
from itertools import izip
from lxml import etree, objectify
from zope.interface import Interface, implements
from time import time
from ldap import DN_FORMAT_LDAPV3
from clacks.common import Environment
from clacks.common.utils import N_
from clacks.common.handler import IInterfaceHandler
from clacks.common.components import Command, Plugin, PluginRegistry
from clacks.agent.objects import ObjectFactory, ObjectProxy, ObjectChanged, SCOPE_BASE, SCOPE_ONE, SCOPE_SUB, ProxyException, ObjectException, SearchWrapper
from clacks.agent.lock import GlobalLock


class IndexScanFinished():
    pass


class FilterException(Exception):
    pass


class IndexException(Exception):
    pass


class ObjectIndex(Plugin):
    """
    The *ObjectIndex* keeps track of objects and their indexed attributes. It
    is the search engine that allows quick querries on the data set with
    paged results and wildcards.
    """
    implements(IInterfaceHandler)

    db = None
    base = None
    _priority_ = 20
    _target_ = 'core'
    _indexed = False
    first_run = False
    to_be_updated = []

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.info("initializing object index handler")
        self.factory = ObjectFactory.getInstance()
        self.__sw = SearchWrapper()

        # Listen for object events
        zope.event.subscribers.append(self.__handle_events)

    def serve(self):
        # Load db instance
        self.db = PluginRegistry.getInstance("XMLDBHandler")

        # if the already exists, check for schema updates!
        schema = self.factory.getXMLObjectSchema(True)
        if self.db.collectionExists("objects") and not self.db.validateSchema('objects', 'objects.xsd', schemaString=schema):
                self.db.dropCollection('objects')
                self.log.info('object definitions changed, dropped old object index collection')

        # Create the database on demand
        if not self.db.collectionExists("objects"):
            self.log.info('created object index collection')
            self.db.createCollection("objects",
                {"o": "http://www.gonicus.de/Objects", "xsi": "http://www.w3.org/2001/XMLSchema-instance"},
                {"objects.xsd": schema})

        # Sync index
        if self.env.config.get("index.disable", "False").lower() != "true":
            sobj = PluginRegistry.getInstance("SchedulerService")
            sobj.getScheduler().add_date_job(self.sync_index,
                    datetime.datetime.now() + datetime.timedelta(seconds=30),
                    tag='_internal', jobstore='ram')

    def stop(self):
        self.db.shutdown()

    def escape(self, data):
        html_escape_table = [
                ("$", "&#36;"), ("{", "&#123;"), ("}", "&#125;"),
                ("(", "&#40;"), (")", "&#41;")]

        for a, b in html_escape_table:
            data = data.replace(a, b)

        return data

    def sync_index(self):
        # Don't index if someone else is already doing it
        if GlobalLock.exists():
            return

        # Don't run index, if someone else already did until the last
        # restart.
        cr = PluginRegistry.getInstance("CommandRegistry")
        nodes = cr.getNodes()
        if len([n for n, v in nodes.items() if 'Indexed' in v and v['Indexed']]):
            return

        GlobalLock.acquire()

        ObjectIndex.first_run = True

        try:
            self._indexed = True

            t0 = time()

            def resolve_children(dn):
                self.log.debug("found object '%s'" % dn)
                res = {}

                children = self.factory.getObjectChildren(dn)
                res = dict(res.items() + children.items())

                for chld in children.keys():
                    res = dict(res.items() + resolve_children(chld).items())

                return res

            self.log.info("scanning for objects")
            res = resolve_children(self.env.base)
            res[self.env.base] = 'dummy'

            self.log.info("generating object index")

            # Find new entries
            backend_objects = []
            for o in sorted(res.keys(), key=len):

                # Get object
                try:
                    obj = ObjectProxy(o)

                except ProxyException as e:
                    self.log.warning("not indexing %s: %s" % (o, str(e)))
                    continue

                except ObjectException as e:
                    self.log.warning("not indexing %s: %s" % (o, str(e)))
                    continue

                # Check for index entry
                changed = self.db.xquery("collection('objects')/*/.[o:UUID = '%s']/o:LastChanged/string()" % obj.uuid)

                # Entry is not in the database
                if not changed:
                    self.insert(obj)

                # Entry is in the database
                else:
                    # OK: already there
                    if obj.modifyTimestamp == datetime.datetime.strptime(changed[0], "%Y-%m-%dT%H:%M:%S"):
                        self.log.debug("found up-to-date object index for %s" % obj.uuid)

                    else:
                        self.log.debug("updating object index for %s" % obj.uuid)
                        self.update(obj)

                backend_objects.append(obj.uuid)
                del obj

            # Remove entries that are in XMLDB, but not in any other backends
            for entry in self.db.xquery("collection('objects')/*/o:UUID/string()"):
                if entry not in backend_objects:
                    self.remove_by_uuid(entry)

            t1 = time()
            self.log.info("processed %d objects in %ds" % (len(res), t1 - t0))

        except Exception as e:
            self.log.critical("building the index failed: %s" % str(e))
            import traceback
            traceback.print_exc()

        finally:
            ObjectIndex.first_run = False

            # Second processing of objects.
            # Some object may have queued themselves to be re-indexed, process them now.
            # (This is necessary to prepare for exmaple the User->groupMembership attribute)
            self.log.info("need to re-run indexing for %d objects" % (len(ObjectIndex.to_be_updated)))
            for uuid in ObjectIndex.to_be_updated:
                dn = self.db.xquery("collection('objects')/*/.[o:UUID = '%s']/o:DN/string()" % uuid)
                if dn:
                    obj = ObjectProxy(dn[0].decode("utf-8"))
                    self.update(obj)
            self.log.info("index re-run finished")

            zope.event.notify(IndexScanFinished())
            GlobalLock.release()

    def index_active(self):
        return self._indexed

    def __handle_events(self, event):

        if isinstance(event, ObjectChanged):
            uuid = event.uuid

            if event.reason == "post remove":
                self.log.debug("removing object index for %s" % uuid)
                self.remove_by_uuid(uuid)

            if event.reason == "post move":
                self.log.debug("updating object index for %s" % uuid)
                obj = ObjectProxy(event.dn)
                self.update(obj)

            if event.reason == "post create":
                self.log.debug("creating object index for %s" % uuid)
                obj = ObjectProxy(event.dn)
                self.insert(obj)

            if event.reason in ["post retract", "post update", "post extend"]:
                self.log.debug("updating object index for %s" % uuid)
                if not event.dn:
                    event.dn = self.db.xquery("collection('objects')/*/.[o:UUID/string() = '%s']/o:DN/string()" % event.uuid)[0]

                obj = ObjectProxy(event.dn)
                self.update(obj)

            self.db.syncCollection('objects')

    def insert(self, obj):
        self.log.debug("creating object index for %s" % obj.uuid)

        # If this is the root node, add the root document
        if self.db.documentExists('objects', obj.uuid):
            raise IndexException("Object with UUID %s already exists" % obj.uuid)

        self.db.addDocument('objects', obj.uuid, self.escape(obj.asXML(True)))

    def remove(self, obj):
        self.remove_by_uuid(obj.uuid)

    def remove_by_uuid(self, entry):
        self.log.debug("removing object index for %s" % entry)
        if self.db.documentExists('objects', entry):
            self.db.deleteDocument('objects', entry)

    def update(self, obj):
        # Gather information
        current = obj.asXML(True)
        saved = self.db.xquery("collection('objects')/*/.[o:UUID = '%s']" % obj.uuid)
        if not saved:
            raise IndexException("No such object %s" % obj.uuid)

        # Convert result set into handy objects
        current = objectify.fromstring(current)
        saved = objectify.fromstring(saved[0])

        # Has the entry been moved?
        if current.DN.text != saved.DN.text:

            # Remove old entry and insert new
            self.remove_by_uuid(obj.uuid)
            self.db.addDocument('objects', obj.uuid, self.escape(obj.asXML(True)))

            # Adjust all DN/ParentDN entries of child objects
            res = iter(self.db.xquery("""let $doc := collection('objects')
                for $x in
                    $doc/*/.[ends-with(o:ParentDN, '%s')]
                return
                    ($x/o:UUID/string(), $x/o:DN/string(), $x/o:ParentDN/string())""" % saved.DN.text))

            # Rewrite every subentry
            for o_uuid, o_dn, o_parent in izip(res, res, res):
                n_dn = o_dn[:-len(saved.DN.text)] + current.DN.text
                n_parent = o_parent[:-len(saved.DN.text)] + current.DN.text

                self.db.xquery("""
                    replace node
                        collection('objects')/*/.[o:UUID = '%s']/o:DN
                    with
                        <o:DN>%s</o:DN>
                    """ % (o_uuid, n_dn))
                self.db.xquery("""
                    replace node
                        collection('objects')/*/.[o:UUID = '%s']/o:ParentDN
                    with
                        <o:ParentDN>%s</o:ParentDN>
                    """ % (o_uuid, n_parent))

        # Move extensions
        if len(self.db.xquery("collection('objects')/*/.[o:UUID = '%s']/o:Extensions" % obj.uuid)) != 0:
            if len(current.findall("Extensions")) > 0:
              self.db.xquery("""
              replace node
                  collection('objects')/*/.[o:UUID = '%s']/o:Extensions
              with
                  %s
              """ % (obj.uuid, self.escape(etree.tostring(current.Extensions))))

            else:
              # Remove extension entry
              self.db.xquery("""
                delete nodes
                   collection('objects')/*/.[o:UUID = '%s']/o:Extensions
                """ % obj.uuid)

        # Move attributes
        if len(self.db.xquery("collection('objects')/*/.[o:UUID = '%s']/o:Attributes" % obj.uuid)) != 0:
          self.db.xquery("""
          replace node
              collection('objects')/*/.[o:UUID = '%s']/o:Attributes
          with
              %s
          """ % (obj.uuid, self.escape(etree.tostring(current.Attributes))))

        # Set LastChanged
        self.db.xquery("""
        replace node
            collection('objects')/*/.[o:UUID = '%s']/o:LastChanged
        with
            <o:LastChanged>%s</o:LastChanged>
        """ % (obj.uuid, current.LastChanged.text))

    @Command(__help__=N_("Perform a raw xquery on the collections"))
    def xquery_dict(self, query):
        """
        Perform a xquery on the object database.

        ========== ==================
        Parameter  Description
        ========== ==================
        xquery     Definition of the search/action
        ========== ==================

        ``Return``: dict
        """
        return self.db.xquery_dict(query, 'objects', True)

    @Command(__help__=N_("Perform a raw xquery on the collections"))
    def xquery(self, query):
        """
        Perform a raw xquery on the object database.

        ========== ==================
        Parameter  Description
        ========== ==================
        xquery     Definition of the search/action
        ========== ==================

        ``Return``: array
        """
        return self.db.xquery(query)

    @Command(__help__=N_("Check if an object with the given UUID exists."))
    def exists(self, uuid):
        """
        Do a database query for the given UUID and return an
        existance flag.

        ========== ==================
        Parameter  Description
        ========== ==================
        uuid       Object identifier
        ========== ==================

        ``Return``: True/False
        """
        return self.db.documentExists('objects', uuid)

    @Command(needsUser=True, __help__=N_("Filter for indexed attributes and return the matches."))
    def simple_search(self, user, base, scope, qstring, fltr=None):
        """
        Query the database using the given query string and an optional filter
        dict - and return the result set.

        ========== ==================
        Parameter  Description
        ========== ==================
        base       Query base
        scope      Query scope
        qstring    Query string
        filter     Hash for extra parameters
        ========== ==================

        ``Return``: List of dicts
        """

        if GlobalLock.exists("scan_index"):
            raise FilterException("index rebuild in progress - try again later")

        return self.__sw.simple_search(base, scope, qstring, fltr=fltr, user=user)

    @Command(needsUser=True, __help__=N_("Filter for indexed attributes and return the matches."))
    def search(self, user, qstring):
        """
        Query the database using the given filter and return the
        result set.

        ========== ==================
        Parameter  Description
        ========== ==================
        qstring    Query string
        ========== ==================

        For more information on the query format, consult the ref:`clacks.agent.objects.search`
        documentation.

        ``Return``: List of dicts
        """

        if GlobalLock.exists("scan_index"):
            raise FilterException("index rebuild in progress - try again later")

        return self.__sw.execute(qstring, user=user)
