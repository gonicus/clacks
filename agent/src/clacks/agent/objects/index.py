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
import re
import shlex
import md5
import clacks.agent.objects.renderer
import itertools
import base64
import time
from pymongo import Connection
from zope.interface import implements
from clacks.common import Environment
from clacks.common.utils import N_
from clacks.common.handler import IInterfaceHandler
from clacks.common.components import Command, Plugin, PluginRegistry
from clacks.agent.objects import ObjectFactory, ObjectProxy, ObjectChanged, ProxyException, ObjectException
from clacks.agent.lock import GlobalLock
from clacks.agent.acl import ACLResolver


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

        # Collect value extenders
        self.__value_extender = clacks.agent.objects.renderer.get_renderers()

    def serve(self):
        # Load db instance
        self.db = self.env.get_mongo_db('clacks')

        # If there is already a collection, check if there is a newer schema available
        schema = self.factory.getXMLObjectSchema(True)
        if "objects" in self.db.collection_names() and self.isSchemaUpdated("objects", schema):
            self.db.objects.drop()
            self.log.info('object definitions changed, dropped old object index collection')

        # Create the initial schema information if required
        if not "objects" in self.db.collection_names():
            self.log.info('created object index collection')
            md5s = md5.new()
            md5s.update(schema)
            md5sum = md5s.hexdigest()

            self.db.objects.save({'schema': {'checksum': md5sum}})

        # Sync index
        if self.env.config.get("index.disable", "False").lower() != "true":
            sobj = PluginRegistry.getInstance("SchedulerService")
            sobj.getScheduler().add_date_job(self.sync_index,
                    datetime.datetime.now() + datetime.timedelta(seconds=30),
                    tag='_internal', jobstore='ram')

        # Ensure basic index for the objects
        for index in ['dn', '_uuid', '_last_changed', '_type', '_extensions', '_container']:
            self.db.objects.ensure_index(index)

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
        indices = [x['key'][0][0] for x in self.db.objects.index_information().values()]
        binaries = self.factory.getBinaryAttributes()

        # Remove index that is not in use anymore
        for attr in indices:
            if not attr in used_attrs and not attr in ['dn', '_id', '_uuid', '_last_changed', '_type', '_extensions', '_container']:
                self.log.debug("removing obsolete index for '%s'" % attr)
                self.db.objects.drop_index(attr)

        # Ensure index for all attributes that want an index
        for attr in used_attrs[:39]:

            # Skip non attribute values
            if '%' in attr or attr in binaries:
                self.log.debug("not adding index for '%s'" % attr)
                continue

            # Add index if it doesn't exist already
            if not attr in indices:
                self.log.debug("adding index for '%s'" % attr)
                self.db.objects.ensure_index(attr)

        # Memorize search information for later use
        self.__search_aid = dict(attrs=attrs,
                                 used_attrs=used_attrs,
                                 mapping=mapping,
                                 resolve=resolve,
                                 aliases=aliases)

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
                indexEntry = self.db.objects.find_one({'_uuid': obj.uuid}, {'_last_changed': 1})

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
            for entry in self.db.objects.find({'_uuid': {'$exists': True}}, {'_uuid': 1}):
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
                entry = self.db.objects.find_one({'_uuid': uuid, 'dn': {'$exists': True}}, {'dn': 1})

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
                    entry = self.db.objects.find_one({'_uuid': event.uuid, 'dn': {'$exists': 1}}, {'dn': 1})
                    if entry:
                        event.dn = entry['dn']

                obj = ObjectProxy(event.dn)
                self.update(obj)

    def insert(self, obj):
        self.log.debug("creating object index for %s" % obj.uuid)

        # If this is the root node, add the root document
        if self.db.objects.find_one({'_uuid': obj.uuid}, {'_uuid': 1}):
            raise IndexException("Object with UUID %s already exists" % obj.uuid)

        self.db.objects.save(obj.asJSON(True))

    def remove(self, obj):
        self.remove_by_uuid(obj.uuid)

    def remove_by_uuid(self, uuid):
        self.log.debug("removing object index for %s" % uuid)
        if self.exists(uuid):
            self.db.objects.remove({'_uuid': uuid})

    def update(self, obj):
        # Gather information
        current = obj.asJSON(True)
        saved = self.db.objects.find_one({'_uuid': obj.uuid})
        if not saved:
            raise IndexException("No such object %s" % obj.uuid)

        # Remove old entry and insert new
        self.remove_by_uuid(obj.uuid)
        self.db.objects.save(obj.asJSON(True))

        # Has the entry been moved?
        if current['dn'] != saved['dn']:

            # Adjust all ParentDN entries of child objects
            res = self.db.objects.find(
                {'_parent_dn': re.compile('^(.*,)?%s$' % re.escape(saved['dn']))},
                {'_uuid': 1, 'dn': 1, '_parent_dn': 1})

            for entry in res:
                o_uuid = entry['_uuid']
                o_dn = entry['dn']
                o_parent = entry['_parent_dn']

                n_dn = o_dn[:-len(saved['dn'])] + current['dn']
                n_parent = o_parent[:-len(saved['dn'])] + current['dn']

                self.db.objects.update({'_uuid': o_uuid}, {
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
        return self.db.objects.find_one({'_uuid': uuid}, {'_uuid': 1}) != None

    def __filter_entry(self, user, entry):
        """
        Takes a query entry and decides based on the user what to do
        with the result set.

        ========== ===========================
        Parameter  Description
        ========== ===========================
        user       User ID
        entry      Search entry as hash
        ========== ===========================

        ``Return``: Filtered result entry
        """
        ne = {'dn': entry['dn'], '_type': entry['_type']}
        attrs = self.__search_aid['mapping'][entry['_type']].values()

        for attr in attrs:
            if attr != None and self.__has_access_to(user, entry['dn'], entry['_type'], attr):
                ne[attr] = entry[attr] if attr in entry else None
            else:
                ne[attr] = None

        return ne

    def __has_access_to(self, user, object_dn, object_type, attr):
        """
        Checks whether the given user has access to the given object/attribute or not.
        """
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if user:
            topic = "%s.objects.%s.attributes.%s" % (self.env.domain, object_type, attr)
            return aclresolver.check(user, topic, "r", base=[object_dn])
        else:
            return True

    @Command(needsUser=True, __help__=N_("Filter for indexed attributes and return the matches."))
    def search(self, user, base, scope, qstring, fltr=None):
        """
        Performs a query based on a simple search string consisting of keywords.

        Query the database using the given query string and an optional filter
        dict - and return the result set.

        ========== ==================
        Parameter  Description
        ========== ==================
        base       Query base
        scope      Query scope (SUB, BASE, ONE)
        qstring    Query string
        fltr       Hash for extra parameters
        ========== ==================

        ``Return``: List of dicts
        """
        res = {}
        keywords = None
        fallback = fltr and "fallback" in fltr and fltr["fallback"]

        # Bail out for empty searches
        if not qstring:
            return []

        # Set defaults
        if not fltr:
            fltr = {}
        if not 'category' in fltr:
            fltr['category'] = "all"
        if not 'secondary' in fltr:
            fltr['secondary'] = "enabled"
        if not 'mod-time' in fltr:
            fltr['mod-time'] = "all"

        try:
            keywords = [s.strip("'").strip('"') for s in shlex.split(qstring)]
        except ValueError:
            keywords = [s.strip("'").strip('"') for s in qstring.split(" ")]
        qstring = qstring.strip("'").strip('"')
        keywords.append(qstring)

        # Make keywords unique
        keywords = list(set(keywords))

        # Sanity checks
        scope = scope.upper()
        if not scope in ["SUB", "BASE", "ONE"]:
            raise Exception("invalid scope - needs to be one of SUB, BASE or ONE")
        if not fltr['mod-time'] in ["hour", "day", "week", "month", "year", "all"]:
            raise Exception("invalid scope - needs to be one of SUB, BASE or ONE")

        # Build query: assemble keywords
        _s = ""
        if fallback:
            _s = re.compile('^.*(' + ("|".join([re.escape(p) for p in keywords])) + ').*$', re.IGNORECASE)
        else:
            _s = {'$in': keywords}

        # Build query: join attributes and keywords
        queries = []
        for typ in self.__search_aid['attrs'].keys():

            # Only filter for cateogry if desired
            if not ("all" == fltr['category'] or typ == fltr['category']):
                continue

            attrs = self.__search_aid['attrs'][typ]

            if len(attrs) == 0:
                continue
            if len(attrs) == 1:
                queries.append({'_type': typ, attrs[0]: _s})
            if len(attrs) > 1:
                queries.append({'_type': typ, "$or": map(lambda a: {a: _s}, attrs)})

        # Build query: assemble
        query = ""
        if scope == "SUB":
            query = {"dn": re.compile("^(.*,)?" + re.escape(base) + "$"), "$or": queries}

        elif scope == "ONE":
            query = {"dn": base, "_parent_dn": base, "$or": queries}

        else:
            query = {"dn": base, "$or": queries}

        # Build query: eventually extend with timing information
        td = None
        if fltr['mod-time'] != "all":
            now = datetime.datetime.now()
            if fltr['mod-time'] == 'hour':
                td = now - datetime.timedelta(hours=1)
            elif fltr['mod-time'] == 'day':
                td = now - datetime.timedelta(days=1)
            elif fltr['mod-time'] == 'week':
                td = now - datetime.timedelta(weeks=1)
            elif fltr['mod-time'] == 'month':
                td = now - datetime.timedelta(days=31)
            elif fltr['mod-time'] == 'year':
                td = now - datetime.timedelta(days=365)

            td = {"$gte": time.mktime(td.timetuple())}
            query["_last_changed"] = td

        # Perform primary query and get collect the results
        #TODO:- relevance / map / reduce functionality?
        squery = []
        these = dict([(x, 1) for x in self.__search_aid['used_attrs']])
        these['dn'] = 1
        these['_type'] = 1

        for item in self.db.objects.find(query, these):
            self.__update_res(res, item, user)

            # Collect information for secondary search?
            if fltr['secondary'] != "enabled":
                continue

            for r in self.__search_aid['resolve'][item['_type']]:
                if r['attribute'] in item:
                    tag = r['type'] if r['type'] else item['_type']

                    # If a category was choosen and it does not fit the
                    # desired target tag - skip that one
                    if not (fltr['category'] == "all" or fltr['category'] == tag):
                        continue

                    squery.append({'_type': tag, r['filter']: {'$in': item[r['attribute']]}})


        # Perform secondary query and update the result
        if fltr['secondary'] == "enabled" and squery:
            query = {"$or": squery}

            # Add "_last_changed" information to query
            if fltr['mod-time'] != "all":
                query["_last_changed"] = td

            # Execute query and update results
            for item in self.db.objects.find(query, these):
                self.__update_res(res, item, user)

        return res.values()

#    def __make_relevance(self, tag, qstring, o_qstring, keywords, secondary=False, fuzzy=False):
#        relevance = 1
#
#        # Penalty for not having an exact match
#        if qstring != o_qstring:
#            relevance *= 2
#
#        # Penalty for not having an case insensitive match
#        if qstring.lower() != o_qstring.lower():
#            relevance *= 4
#
#        # Penalty for not having tag in keywords
#        if not set([t.lower() for t in tag]).intersection(set([k.lower() for k in keywords])):
#            relevance *= 6
#
#        # Penalty for secondary
#        if secondary:
#            relevance *= 10
#
#        # Penalty for fuzzyness
#        if fuzzy:
#            relevance *= 10
#
#        return relevance

    def __update_res(self, res, item, user=None):
        relevance = 0

        # Filter out what the current use is not allowed to see
        item = self.__filter_entry(user, item)
        if not item or item['dn'] == None:
            # We've obviously no permission to see thins one - skip it
            return

        if item['dn'] in res:
            #TODO: we may need to update the relevance information
            #dn = item['dn']
            #if res[dn]['relevance'] > relevance:
            #    res[dn]['relevance'] = relevance
            return

        entry = {'tag': item['_type'], 'relevance': relevance}
        for k, v in self.__search_aid['mapping'][item['_type']].items():
            if k:
                if k == "icon":
                    continue
                if v in item and item[v]:
                    if v == "dn":
                        entry[k] = item[v]
                    else:
                        entry[k] = item[v][0]
                else:
                    entry[k] = self.__build_value(v, item)

            entry['icon'] = None

            #TODO: build server side caching and transfer an URL instead of
            #icon_attribute = self.__search_aid['mapping'][item['_type']]['icon']
            #if icon_attribute and icon_attribute in item and item[icon_attribute]:
            #    entry['icon'] = "data:image/jpeg;base64," + base64.b64encode(item[icon_attribute][0])

        res[item['dn']] = entry

    def __build_value(self, v, info):
        """
        Fill placeholders in the value to be displayed as "description".
        """

        if not v:
            return ""

        # Find all placeholders
        attrs = {}
        for attr in re.findall(r"%\(([^)]+)\)s", v):

            # Extract ordinary attributes
            if attr in info:
                attrs[attr] = ", ".join(info[attr])

            # Check for result renderers
            elif attr in self.__value_extender:
                attrs[attr] = self.__value_extender[attr](info)

            # Fallback - just set nothing
            else:
                attrs[attr] = ""

        # Assemble and remove empty lines and multiple whitespaces
        res = v % attrs
        res = re.sub(r"(<br>)+", "<br>", res)
        res = re.sub(r"^<br>", "", res)
        res = re.sub(r"<br>$", "", res)
        return "<br>".join([s.strip() for s in res.split("<br>")])

    def raw_search(self, query, conditions):
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
            raise FilterException("index rebuild in progress - try again later")

        return self.db.objects.find(query, conditions)
