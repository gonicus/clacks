# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

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
import re
import md5
import time
import itertools
from zope.interface import implements
from clacks.common import Environment
from clacks.common.utils import N_
from clacks.common.event import EventMaker
from clacks.common.handler import IInterfaceHandler
from clacks.common.components import Command, Plugin, PluginRegistry
from clacks.common.components.amqp import EventConsumer
from clacks.agent.objects import ObjectFactory, ObjectProxy, ObjectChanged, ProxyException, ObjectException
from clacks.agent.error import ClacksErrorHandler as C
from clacks.agent.lock import GlobalLock


# Register the errors handled  by us
C.register_codes(dict(
    OBJECT_EXISTS=N_("Object with UUID %(uuid)s already exists"),
    OBJECT_NOT_FOUND=N_("Cannot find object %(id)s"),
    INDEXING=N_("index rebuild in progress - try again later")
))


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

        # Listen for object events
        zope.event.subscribers.append(self.__handle_events)

    def serve(self):
        # Load db instance
        self.db = self.env.get_mongo_db('clacks')

        # If there is already a collection, check if there is a newer schema available
        schema = self.factory.getXMLObjectSchema(True)
        if "index" in self.db.collection_names() and self.isSchemaUpdated("index", schema):
            self.db.index.drop()
            self.log.info('object definitions changed, dropped old object index collection')

        # Create the initial schema information if required
        if not "index" in self.db.collection_names():
            self.log.info('created object index collection')
            md5s = md5.new()
            md5s.update(schema)
            md5sum = md5s.hexdigest()

            self.db.index.save({'schema': {'checksum': md5sum}})

        # Sync index
        if self.env.config.get("index.disable", "False").lower() != "true":
            sobj = PluginRegistry.getInstance("SchedulerService")
            sobj.getScheduler().add_date_job(self.sync_index,
                    datetime.datetime.now() + datetime.timedelta(seconds=30),
                    tag='_internal', jobstore='ram')

        # Ensure basic index for the objects
        for index in ['dn', '_uuid', '_last_changed', '_type', '_extensions', '_container', '_parent_dn']:
            self.db.index.ensure_index(index)

        # Extract search aid
        attrs = {}
        mapping = {}
        resolve = {}
        aliases = {}

        for otype in self.factory.getObjectTypes():

            # Assemble search aid
            item = self.factory.getObjectSearchAid(otype)

            if not item:
                continue

            typ = item['type']
            aliases[typ] = [typ]

            if not typ in attrs:
                attrs[typ] = []
            if not typ in resolve:
                resolve[typ] = []
            if not typ in mapping:
                mapping[typ] = dict(dn="dn", title="title", description="description", icon=None)

            attrs[typ] += item['search']

            if 'keyword' in item:
                aliases[typ] += item['keyword']
            if 'map' in item:
                mapping[typ].update(item['map'])
            if 'resolve' in item:
                resolve[typ] += item['resolve']

        # Add index for attribute used for filtering and memorize
        # attributes potentially needed for queries.
        tmp = [x for x in attrs.values()]
        used_attrs = list(itertools.chain.from_iterable(tmp))
        used_attrs += list(itertools.chain.from_iterable([x.values() for x in mapping.values()]))
        used_attrs += list(set(itertools.chain.from_iterable([[x[0]['filter'], x[0]['attribute']] for x in resolve.values()])))
        used_attrs = list(set(used_attrs))

        # Remove potentially not assigned values
        used_attrs = [u for u in used_attrs if u]

        # Prepare index
        indices = [x['key'][0][0] for x in self.db.index.index_information().values()]
        binaries = self.factory.getBinaryAttributes()

        # Remove index that is not in use anymore
        for attr in indices:
            if not attr in used_attrs and not attr in ['dn', '_id', '_uuid', '_last_changed', '_type', '_extensions', '_container', '_parent_dn']:
                self.log.debug("removing obsolete index for '%s'" % attr)
                self.db.index.drop_index(attr)

        # Ensure index for all attributes that want an index
        for attr in used_attrs[:39]:

            # Skip non attribute values
            if '%' in attr or attr in binaries:
                self.log.debug("not adding index for '%s'" % attr)
                continue

            # Add index if it doesn't exist already
            if not attr in indices:
                self.log.debug("adding index for '%s'" % attr)
                self.db.index.ensure_index(attr)

        # Memorize search information for later use
        self.__search_aid = dict(attrs=attrs,
                                 used_attrs=used_attrs,
                                 mapping=mapping,
                                 resolve=resolve,
                                 aliases=aliases)

        # Add event processor
        amqp = PluginRegistry.getInstance('AMQPHandler')
        EventConsumer(self.env,
            amqp.getConnection(),
            xquery="""
                declare namespace f='http://www.gonicus.de/Events';
                let $e := ./f:Event
                return $e/f:BackendChange
            """,
            callback=self.__backend_change_processor)

    def __backend_change_processor(self, data):
        """
        This method gets called if an external backend reports
        a modification of an entry under its hood.

        We use it to update / create / delete existing index
        entries.
        """
        data = data.BackendChange
        dn = data.DN.text if hasattr(data, 'DN') else None
        new_dn = data.NewDN.text if hasattr(data, 'NewDN') else None
        change_type = data.ChangeType.text
        _uuid = data.UUID.text if hasattr(data, 'UUID') else None
        _last_changed = datetime.datetime.strptime(data.ModificationTime.text, "%Y%m%d%H%M%SZ")

        # Resolve dn from uuid if needed
        if not dn:
            entry = self.db.index.find_one({'_uuid': _uuid}, {'dn': 1})
            if entry:
                dn = entry['dn']

        # Modification
        if change_type == "modify":

            # Get object
            obj = self._get_object(dn)
            if not obj:
                return

            # Check if the entry exists - if not, maybe let create it
            entry = self.db.index.find_one({'$or': [{'dn': re.compile(r'^%s$' %
                re.escape(dn), re.IGNORECASE)}, {'_uuid': _uuid}]}, {'_last_changed': 1})

            if entry:
                self.update(obj)

            else:
                self.insert(obj)

        # Add
        if change_type == "add":

            # Get object
            obj = self._get_object(dn)
            if not obj:
                return

            self.insert(obj)

        # Delete
        if change_type == "delete":
            self.log.info("object has changed in backend: indexing %s" % dn)
            self.log.warning("external delete might not take care about references")
            self.db.index.remove({'dn': dn})

        # Move
        if change_type in ['modrdn', 'moddn']:

            # Get object
            obj = self._get_object(new_dn)
            if not obj:
                return

            # Check if the entry exists - if not, maybe let create it
            entry = self.db.index.find_one({'$or': [{'dn': re.compile(r'^%s$' % re.escape(new_dn), re.IGNORECASE)}, {'_uuid': _uuid}]}, {'_last_changed': 1})

            if entry and obj:
                self.update(obj)

            else:
                self.insert(obj)

    def _get_object(self, dn):
        try:
            obj = ObjectProxy(dn)

        except ProxyException as e:
            self.log.warning("not found %s: %s" % (obj, str(e)))
            obj = None

        except ObjectException as e:
            self.log.warning("not indexing %s: %s" % (obj, str(e)))
            obj = None

        return obj

    def get_search_aid(self):
        return self.__search_aid

    def isSchemaUpdated(self, collection, schema):
        # Calculate md5 checksum for potentially new schema
        md5s = md5.new()
        md5s.update(schema)
        md5sum = md5s.hexdigest()

        # Load stored checksum of current schema from the collection
        old_md5sum = None
        tmp = self.db[collection].find_one({'schema.checksum': {'$exists': True}}, {'schema.checksum': 1})
        if tmp:
            old_md5sum = tmp['schema']['checksum']

        return old_md5sum != md5sum

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

            t0 = time.time()

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
                indexEntry = self.db.index.find_one({'_uuid': obj.uuid}, {'_last_changed': 1})

                # Entry is not in the database
                if not indexEntry:
                    self.insert(obj)

                # Entry is in the database
                else:
                    # OK: already there
                    if obj.modifyTimestamp == indexEntry['_last_changed']:
                        self.log.debug("found up-to-date object index for %s" % obj.uuid)

                    else:
                        self.log.debug("updating object index for %s" % obj.uuid)
                        self.update(obj)

                backend_objects.append(obj.uuid)
                del obj

            # Remove entries that are in the index, but not in any other backends
            for entry in self.db.index.find({'_uuid': {'$exists': True}}, {'_uuid': 1}):
                if entry['_uuid'] not in backend_objects:
                    self.remove_by_uuid(entry['_uuid'])

            t1 = time.time()
            self.log.info("processed %d objects in %ds" % (len(res), t1 - t0))

        except Exception as e:
            self.log.critical("building the index failed: %s" % str(e))
            import traceback
            traceback.print_exc()

        finally:
            ObjectIndex.first_run = False

            # Some object may have queued themselves to be re-indexed, process them now.
            self.log.info("need to refresh index for %d objects" % (len(ObjectIndex.to_be_updated)))
            for uuid in ObjectIndex.to_be_updated:
                entry = self.db.index.find_one({'_uuid': uuid, 'dn': {'$exists': True}}, {'dn': 1})

                if entry:
                    obj = ObjectProxy(entry['dn'])
                    self.update(obj)

            self.log.info("index refresh finished")

            zope.event.notify(IndexScanFinished())
            GlobalLock.release()

    def index_active(self):
        return self._indexed

    def __handle_events(self, event):

        if isinstance(event, ObjectChanged):
            change_type = None
            _uuid = event.uuid
            _dn = None
            _last_changed = time.mktime(datetime.datetime.now().timetuple())

            # Try to find the affected DN
            e = self.db.index.find_one({'_uuid': _uuid}, {'dn': 1, '_last_changed': 1})
            if e:

                # New pre-events don't have a dn. Just skip is in this case...
                if 'dn' in e:
                    _dn = e['dn']
                    _last_changed = e['_last_changed']
                else:
                    _dn = "not known yet"
                    _last_changed = datetime.datetime.now()

            if event.reason == "post object remove":
                self.log.debug("removing object index for %s" % _uuid)
                self.remove_by_uuid(_uuid)
                change_type = "remove"

            if event.reason == "post object move":
                self.log.debug("updating object index for %s" % _uuid)
                obj = ObjectProxy(event.dn)
                self.update(obj)
                _dn = obj.dn
                change_type = "move"

            if event.reason == "post object create":
                self.log.debug("creating object index for %s" % _uuid)
                obj = ObjectProxy(event.dn)
                self.insert(obj)
                _dn = obj.dn
                change_type = "create"

            if event.reason in ["post object retract", "post object update", "post object extend"]:
                self.log.debug("updating object index for %s" % _uuid)
                if not event.dn:
                    entry = self.db.index.find_one({'_uuid': _uuid, 'dn': {'$exists': 1}}, {'dn': 1})
                    if entry:
                        event.dn = entry['dn']

                obj = ObjectProxy(event.dn)
                self.update(obj)
                change_type = "update"

            # If there were changes, notify about changed objects
            if change_type:
                amqp = PluginRegistry.getInstance('AMQPHandler')

                e = EventMaker()
                update = e.Event(
                    e.ObjectChanged(
                        e.DN(_dn),
                        e.UUID(_uuid),
                        e.ModificationTime(str(_last_changed)),
                        e.ChangeType(change_type)
                    )
                )
                amqp.sendEvent(update)

    def insert(self, obj):
        self.log.debug("creating object index for %s" % obj.uuid)

        # If this is the root node, add the root document
        if self.db.index.find_one({'_uuid': obj.uuid}, {'_uuid': 1}):
            raise IndexException(C.make_error('OBJECT_EXISTS', "base", uuid=obj.uuid))

        self.db.index.save(obj.asJSON(True))

    def remove(self, obj):
        self.remove_by_uuid(obj.uuid)

    def remove_by_uuid(self, uuid):
        self.log.debug("removing object index for %s" % uuid)
        if self.exists(uuid):
            self.db.index.remove({'_uuid': uuid})

    def update(self, obj):
        # Gather information
        current = obj.asJSON(True)
        saved = self.db.index.find_one({'_uuid': obj.uuid})
        if not saved:
            raise IndexException(C.make_error('OBJECT_NOT_FOUND', "base", uuid=obj.uuid))

        # Remove old entry and insert new
        self.remove_by_uuid(obj.uuid)
        self.db.index.save(obj.asJSON(True))

        # Has the entry been moved?
        if current['dn'] != saved['dn']:

            # Adjust all ParentDN entries of child objects
            res = self.db.index.find(
                {'_parent_dn': re.compile('^(.*,)?%s$' % re.escape(saved['dn']))},
                {'_uuid': 1, 'dn': 1, '_parent_dn': 1})

            for entry in res:
                o_uuid = entry['_uuid']
                o_dn = entry['dn']
                o_parent = entry['_parent_dn']

                n_dn = o_dn[:-len(saved['dn'])] + current['dn']
                n_parent = o_parent[:-len(saved['dn'])] + current['dn']

                self.db.index.update({'_uuid': o_uuid}, {
                        '$set': {'dn': n_dn, '_parent_dn': n_parent}})

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
        return self.db.index.find_one({'_uuid': uuid}, {'_uuid': 1}) != None

    @Command(__help__=N_("Get list of defined base object types."))
    def getBaseObjectTypes(self):
        ret = []
        for k, v in self.factory.getObjectTypes().items():
            if v['base'] == True:
                ret.append(k)

        return ret

    def search(self, query, conditions):
        """
        Perform a raw mongodb find call.

        ========== ==================
        Parameter  Description
        ========== ==================
        query      Query hash
        conditions Conditions hash
        ========== ==================

        For more information on the query format, consult the mongodb documentation.

        ``Return``: List of dicts
        """

        if GlobalLock.exists("scan_index"):
            raise FilterException(C.make_error('INDEXING', "base"))

        return self.db.index.find(query, conditions)
