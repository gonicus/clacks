# -*- coding: utf-8 -*-
"""
Object Index
============

The Object Index is the search engine in GOsa. It keeps track about
all defined object types and can find references to it inside of its
local index database

----
"""
import re
import inspect
import sqlalchemy.sql
import logging
import collections
import ldap.dn
import zope.event
import datetime
from zope.interface import implements
from time import time
from base64 import b64encode, b64decode
from ldap import DN_FORMAT_LDAPV3
from gosa.common import Environment
from gosa.common.utils import N_
from gosa.common.handler import IInterfaceHandler
from gosa.common.components import Command, Plugin, PluginRegistry
from gosa.agent.objects import GOsaObjectFactory, GOsaObjectProxy, ObjectChanged, SCOPE_BASE, SCOPE_ONE, SCOPE_SUB, ProxyException, ObjectException
from gosa.agent.lock import GlobalLock
from gosa.agent.xmldb import XMLDBHandler
from gosa.agent.ldap_utils import LDAPHandler

#TODO: to be removed
from sqlalchemy.sql import select, and_, or_, func, asc, desc
from sqlalchemy.dialects.sqlite.base import SQLiteDialect
from sqlalchemy import Table, Column, Integer, Boolean, String, DateTime, Date, Unicode, MetaData


class FilterException(Exception):
    pass


class ObjectIndex(Plugin):
    """
    The *ObjectIndex* keeps track of objects and their indexed attributes. It
    is the search engine that allows quick querries on the data set with
    paged results and wildcards.
    """
    implements(IInterfaceHandler)

    __type_conv = {
            'Integer': Integer,
            'Boolean': Boolean,
            'String': String(1024),
            'UnicodeString': Unicode(1024),
            'Date': Date,
            'Timestamp': DateTime,
            }
    _priority_ = 20
    _target_ = 'core'
    _indexed = False

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.info("initializing object index handler")
        self.factory = GOsaObjectFactory.getInstance()

        # Listen for object events
        zope.event.subscribers.append(self.__handle_events)

    def serve(self):
        # Load db instance
        self.db = PluginRegistry.getInstance("XMLDBHandler")

        #TODO: for the initial testing, always drop the collection to
        #      have a clean start
        if self.db.collectionExists("objects"):
            self.db.dropCollection("objects")

        schema = self.factory.getXMLObjectSchema(True)
        self.db.createCollection("objects",
            {"o": "http://www.gonicus.de/Objects", "xsi": "http://www.w3.org/2001/XMLSchema-instance"},
            {"objects.xsd": schema})

        # Sync index
        if self.env.config.get("index.disable", "False").lower() != "true":
            sobj = PluginRegistry.getInstance("SchedulerService")
            sobj.getScheduler().add_date_job(self.sync_index,
                    datetime.datetime.now() + datetime.timedelta(seconds=30),
                    tag='_internal', jobstore='ram')

    def escape(data):
        html_escape_table = [
                ("$", "&#36;"), ("{", "&#123;"), ("}", "&#125;"),
                ("(", "&#40;"), (")", "&#41;")]

        for a, b in html_escape_table:
            data = data.replace(a, b)

        return data

    def sync_index(self):
        # Don't index if someone else is already doing it
        print "------> TODO: re-enable me!"
        #if GlobalLock.exists():
        #    return

        # Don't run index, if someone else already did until the last
        # restart.
        cr = PluginRegistry.getInstance("CommandRegistry")
        nodes = cr.getNodes()
        if len([n for n, v in nodes.items() if 'Indexed' in v and v['Indexed']]):
            return

        #GlobalLock.acquire()
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
        res = resolve_children(LDAPHandler.get_instance().get_base())

        self.log.info("generating object index")

        # Find new entries
        backend_objects = []
        for o in res.keys():

            # Get object
            try:
                obj = GOsaObjectProxy(o)

            except ProxyException as e:
                self.log.warning("not indexing %s: %s" % (o, str(e)))
                continue

            except ObjectException as e:
                self.log.warning("not indexing %s: %s" % (o, str(e)))
                continue

            # Check for index entry
            changed = self.db.xquery("collection('objects')/*[UUID/string() = '%s']/LastChanged/string()" % obj.uuid)

            # Entry is not in the database
            if not changed:
                self.log.debug("creating object index for %s" % obj.uuid)
                self.db.addDocument('objects', obj.uuid, obj.asXML(True))

                #TODO: maintain structure

            # Entry is in the database
            else:
                # OK: already there
                if obj.modifyTimestamp == datetime.strptime(changed[0], "%Y-%m-%d %H:%M:%S"):
                    self.log.debug("found up-to-date object index for %s" % obj.uuid)

                else:
                    self.log.debug("updating object index for %s" % obj.uuid)
                    self.db.xquery("replace node doc('dbxml:/objects/%s')/* with %s" % (obj.uuid, escape(obj.asXML(True))))

                    #TODO: maintain structure

            backend_objects.append(obj.uuid)
            del obj

        # Remove entries that are in XMLDB, but not in any other backends
        for entry in self.db.getDocuments('objects'):
            if entry not in backend_objects:
                self.log.debug("removing object index for %s" % entry)
                self.db.deleteDocument('objects', entry)

                #TOOD: maintain structure

        t1 = time()
        self.log.info("processed %d objects in %ds" % (len(res), t1 - t0))
        GlobalLock.release()

# TODO:-to-be-revised--------------------------------------------------------------------------------------

    def index_active(self):
        return self._indexed

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
        tmp = self.__conn.execute(select([self.__index.c._uuid], self.__index.c._uuid == uuid))
        res = bool(tmp.fetchone())
        tmp.close()
        return res

    def insert(self, uuid, dn, **props):
        props['_uuid'] = uuid
        props['_dn']= self.dn2b64(dn)
        prnt_helper = props['_dn'].split(",")
        props['_parent_dn'] = ",".join(prnt_helper[1:]) if len(prnt_helper) > 1 else ""

        # Convert all list types to Unicode strings
        props = dict([(attr, self.__sep + self.__sep.join(key) + self.__sep if type(key) == list else key) for attr, key in props.items()])
        self.__conn.execute(self.__index.insert(), [props])

    def remove(self, uuid):
        self.__conn.execute(self.__index.delete().where(self.__index.c._uuid == uuid))

    def move(self, uuid, dn):
        self.update(uuid, _dn=dn)

    def update(self, uuid, **props):
        if '_dn'  in props:
            props['_dn']= self.dn2b64(props['_dn'])
            prnt_helper = props['_dn'].split(",")
            props['_parent_dn'] = ",".join(prnt_helper[1:]) if len(prnt_helper) > 1 else ""

        props = dict([(attr, self.__sep + self.__sep.join(key) + self.__sep if type(key) == list else key) for attr, key in props.items()])
        self.__conn.execute(self.__index.update().where(self.__index.c._uuid == uuid), [props])

    @Command(__help__=N_("Filter for indexed attributes and return the number of matches."))
    def count(self, base=None, scope=SCOPE_SUB, fltr=None):
        """
        Query the database using the given filter and return the number
        of matches.

        ========== ==================
        Parameter  Description
        ========== ==================
        base       Base to search on
        scope      Scope to use (BASE, ONE, SUB)
        fltr       Filter description
        ========== ==================

        Filter example:

         {
           '_and': {
             'uid': 'foo',
             'givenName': u'Klaus',
             '_or': {
               '_in': {
                 'sn': [u'Mustermann', u'Musterfrau']
               },
               '_lt': ['dateOfBirth', datetime.datetime.now()]
             }
           }
         }

        Available filter parameters:

        ============ ==================
        Parameter    Description
        ============ ==================
        [a-zA-Z0-9]+ Ordinary match condition, maps to a single value
        _and         And condition, maps to more conditions
        _or          Or condition, maps to more conditions
        _not         Not condition, inverts condition
        _gt          Check if value is greater, maps to a 2 value list
        _ge          Check if value is greater or equal, maps to a 2 value list
        _lt          Check if value is lesser, maps to a 2 value list
        _le          Check if value is lesser or equal, maps to a 2 value list
        ============ ==================

        ``Return``: Integer
        """
        if GlobalLock.exists("scan_index"):
            raise FilterException("index rebuild in progress - try again later")

        base_filter = None

        if scope == None or not scope in [SCOPE_ONE, SCOPE_BASE, SCOPE_SUB]:
            raise FilterException("invalid search scope")

        if base:
            base = self.dn2b64(base)
            if scope == SCOPE_BASE:
                base_filter = self.__index.c._dn == base

            if scope == SCOPE_ONE:
                base_filter = or_(self.__index.c._dn == base, self.__index.c._parent_dn == base)

            if scope == SCOPE_SUB:
                base_filter = or_(self.__index.c._dn == base, self.__index.c._parent_dn.like("%%,%s" % base))

        if fltr:
            if base:
                fltr = and_(base_filter, *self.__build_filter(fltr))
            else:
                fltr = self.__build_filter(fltr)

            slct = select([func.count(self.__index.c._uuid)], fltr)

        else:
            if base:
                slct = select([func.count(self.__index.c._uuid)], base_filter)
            else:
                slct = select([func.count(self.__index.c._uuid)])

        return self.__conn.execute(slct).fetchone()[0]

    @Command(__help__=N_("Filter for indexed attributes and return the matches."))
    def search(self, base=None, scope=SCOPE_SUB, fltr=None, attrs=None, begin=None, end=None, order_by=None, descending=False):
        """
        Query the database using the given filter and return the
        result set.

        ========== ==================
        Parameter  Description
        ========== ==================
        base       Base to search on
        scope      Scope to use (BASE, ONE, SUB)
        fltr       Filter description
        attrs      List of attributes the result set should contain
        begin      Offset to start returning results
        end        End offset to stop returning results
        order_by   Attribute to sort for
        descending Ascending or descending sort
        ========== ==================

        For more information on the filter format, consult the ref:`gosa.agent.objects.index.count`
        documentation.

        ``Return``: List of dicts
        """
        if GlobalLock.exists("scan_index"):
            raise FilterException("index rebuild in progress - try again later")

        base_filter = None

        if not attrs:
            ats = [self.__index]
        else:
            ats = []
            for a in attrs:
                ats.append(getattr(self.__index.c, a))

        if base:
            base = self.dn2b64(base)
            if scope == SCOPE_BASE:
                base_filter = self.__index.c._dn == base

            if scope == SCOPE_ONE:
                base_filter = or_(self.__index.c._dn == base, self.__index.c._parent_dn == base)

            if scope == SCOPE_SUB:
                base_filter = or_(self.__index.c._dn == base, self.__index.c._parent_dn.like("%%,%s" % base))

        if fltr:
            if base:
                sl = select(ats, and_(base_filter, *self.__build_filter(fltr)))
            else:
                sl = select(ats, *self.__build_filter(fltr))
        else:
            if base:
                sl = select(ats, base_filter)
            else:
                sl = select(ats)

        # Apply ordering
        if order_by:
            if descending:
                sl = sl.order_by(desc(order_by))
            else:
                sl = sl.order_by(asc(order_by))

        # Apply range
        if begin != None and end != None:
            if begin >= end:
                raise FilterException("filter range error - 'begin' is not < 'end'")

            sl = sl.offset(begin).limit(end - begin + 1)

        res = [dict(r.items()) for r in self.__conn.execute(sl).fetchall()]
        return self.__convert_lists(res)

    def __convert_lists(self, data):
        if isinstance(data, str) or isinstance(data, unicode):
            # Check for list conversion
            if data[0] == self.__sep and data[-1] == self.__sep:
                return self.__bl.findall(data)
            return data
        elif isinstance(data, collections.Mapping):
            return dict(map(self.__convert_lists, data.iteritems()))
        elif isinstance(data, collections.Iterable):
            if len(data) and data[0] == "_dn":
                data = (data[0], self.b642dn(data[1]))
            return type(data)(map(self.__convert_lists, data))
        else:
            return data

    def __build_filter(self, fltr):
        arg = []

        for el, value in fltr.items():
            cel = el
            value = value.replace("*", "%")

            if el in ["_and", "_or", "_not"]:
                if type(value) == dict:
                    v = getattr(sqlalchemy.sql, el[1:] + "_")(*self.__build_filter(value))
                    arg.append(v)
                else:
                    raise FilterException("operator needs a dict argument")

            elif el in ["_gt", "_lt", "_ge", "_le"]:
                if len(value) != 2:
                    raise FilterException("operator needs a list with exactly two parameters")

                if type(value) == list and len(value) == 2:
                    if el == "_gt":
                        arg.append(getattr(self.__index.c, value[0]) > value[1])
                    if el == "_lt":
                        arg.append(getattr(self.__index.c, value[0]) < value[1])
                    if el == "_ge":
                        arg.append(getattr(self.__index.c, value[0]) >= value[1])
                    if el == "_le":
                        arg.append(getattr(self.__index.c, value[0]) <= value[1])
                else:
                    raise FilterException("operator needs a list with exactly two parameters")

            elif el == "_in":
                if len(value) != 1:
                    raise FilterException("operator expects a single list argument")

                k, v = value.items()[0]
                if type(v) != list:
                    raise FilterException("operator expects a single list argument")

                arg.append(getattr(self.__index.c, k).in_(v))

            elif el == "type":
                arg.append(or_(self.__index.c._type == value, self.__index.c._extensions.op('regexp')(r"\%s%s\%s" % (self.__sep, value, self.__sep))))

            elif el == "uuid":
                arg.append(or_(self.__index.c._uuid == value, self.__index.c._extensions.op('regexp')(r"\%s%s\%s" % (self.__sep, value, self.__sep))))

            elif not cel in self.__types:
                raise FilterException("attribute '%s' is not indexed" % cel)

            elif self.__types[cel]['multivalue']:
                if '%' in value:
                    value = value.replace('%', r'[^\%s]*' % self.__sep)

                arg.append(getattr(self.__index.c, cel).op('regexp')(r"\%s%s\%s" % (self.__sep, value, self.__sep)))

            else:
                if '%' in value:
                    arg.append(getattr(self.__index.c, cel).like(value))
                else:
                    arg.append(getattr(self.__index.c, cel) == value)

        return arg

    def dn2b64(self, dn):
        parts = ldap.dn.explode_dn(dn.encode('utf-8').lower(), flags=DN_FORMAT_LDAPV3)
        return ",".join([b64encode(p) for p in parts])

    def b642dn(self, b64dn):
        return u",".join([b64decode(p).decode('utf-8') for p in b64dn.split(",")])


    def __handle_events(self, event):
        uuid = event.uuid
        if isinstance(event, ObjectChanged):
            uuid = event.uuid
            f = GOsaObjectFactory.getInstance()

            if event.reason == "post remove":
                self.log.debug("removing object index for %s" % uuid)
                self.remove(uuid)

            if event.reason == "post move":
                self.log.debug("updating object index for %s" % uuid)
                self.move(uuid, event.dn)

            if event.reason == "post create":
                self.log.debug("creating object index for %s" % uuid)
                o_type, ext = f.identifyObject(event.dn)
                obj = f.getObject(o_type, event.dn)

                # Gather index attributes
                attrs = {}
                for attr in self.index_attrs:
                    if obj.hasattr(attr):
                        attrs[attr] = getattr(obj, attr)

                self.insert(uuid, event.dn, _lastChanged=obj.modifyTimestamp, _type=o_type, _extensions=ext, **attrs)

            if event.reason in ["post retract", "post update", "post extend"]:
                self.log.debug("updating object index for %s" % uuid)

                # Eventually try to resolve the DN for non base objects
                if not event.dn:
                    event.dn = self.search(fltr={'uuid': uuid}, attrs=['_dn'])[0]['_dn']

                o_type, ext = f.identifyObject(event.dn)
                obj = f.getObject(o_type, event.dn)

                # Gather index attributes
                attrs = {}
                for attr in self.index_attrs:
                    if obj.hasattr(attr):
                        attrs[attr] = getattr(obj, attr)

                attrs['_dn']= event.dn
                self.update(uuid, _type=o_type, _lastChanged=obj.modifyTimestamp, _extensions=ext, **attrs)
