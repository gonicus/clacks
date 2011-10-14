# -*- coding: utf-8 -*-
import re
import inspect
import sqlalchemy.sql
import logging
import collections
import ldap.dn
from time import time
from base64 import b64encode, b64decode
from ldap import DN_FORMAT_LDAPV3
from gosa.common import Environment
from gosa.common.utils import N_
from gosa.common.components import Command, Plugin
from gosa.agent.objects import GOsaObjectFactory, SCOPE_BASE, SCOPE_ONE, SCOPE_SUB
from sqlalchemy.sql import select, and_, or_, func, asc
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
    __type_conv = {
            'Integer': Integer,
            'Boolean': Boolean,
            'String': String(1024),
            'UnicodeString': Unicode(1024),
            'Date': Date,
            'Timestamp': DateTime,
            }
    __sep = '|'
    __types = None
    __engine = None
    __conn = None
    __fixed = ['id', '_dn', '_parent_dn', '_uuid', '_lastChanged', '_extensions', '_type']
    _priority_ = 20
    _target_ = 'core'

    def __init__(self, run_index=True):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.info("initializing object index handler")
        self.factory = GOsaObjectFactory.getInstance()

        self.__bl = re.compile(r'([^%s]+)' % self.__sep)

        # Define attributes to be indexed from configuration
        index_attrs = [s.strip() for s in self.env.config.get("index.attributes").split(",")]
        available_attrs = self.factory.getAttributes()

        self.__types = {}
        for ia in index_attrs:
            if not ia in available_attrs:
                self.log.warning("attribute '%s' is not available" % ia)
                continue

            self.__types[ia] = available_attrs[ia]

        self.__engine = self.env.getDatabaseEngine('index')

        # Table name
        idx = self.env.config.get("index.table", default="index")

        # Load current database setup
        meta = MetaData(self.__engine)
        meta.reflect()

        reset = True
        if idx in meta.tables:
            current_attrs = set(self.__types.keys())
            db_attrs = set([str(x)[len(idx) + 1:] for x in meta.tables[idx].columns if not str(x)[len(idx) + 1:] in self.__fixed])

            if current_attrs == db_attrs:

                for attr in db_attrs:

                    # Check if we at least subclass the type we got from the
                    # database
                    s_type = type(getattr(meta.tables[idx].columns, attr).type)
                    try:
                        d_type = self.__type_conv[self.__types[attr]['type']]
                        if not inspect.isclass(d_type):
                            d_type = d_type.__class__

                    except KeyError:
                        self.log.warning("type '%s' not supported in index - skipping" % self.__types[attr]['type'])
                        continue

                    if (not issubclass(s_type, d_type)):

                        # If that fails, maybe there's one other try in the
                        # class hierachy
                        superiours = inspect.getmro(d_type)
                        if not (len(superiours) > 1 and issubclass(s_type, superiours[1])):
                            break
                else:
                    reset = False

        # Create schema for storing indexed attributes
        if reset and idx in meta.tables:
            self.log.info("index attributes changed - clearing index table")
            meta.tables[idx].drop(checkfirst=False)
            del meta

        metadata = MetaData()

        props = []
        for attr in self.__types.keys():
            try:
                d_type = self.__type_conv[self.__types[attr]['type']]
            except KeyError:
                self.log.warning("type '%s' not supported in index - skipping" % self.__types[attr]['type'])
                continue
            props.append(Column(attr, d_type))

        self.__index = Table(idx, metadata,
            Column('_uuid', String(36), primary_key=True),
            Column('_dn', String(1024)),
            Column('_parent_dn', String(1024)),
            Column('_lastChanged', DateTime),
            Column('_type', String(256)),
            Column('_extensions', String(256)),
            *props)

        metadata.create_all(self.__engine)

        # Establish the connection
        self.__conn = self.__engine.connect()

        # SQlite needs a custom regex function
        if issubclass(type(self.__engine.dialect), SQLiteDialect):

            def sqlite_regexp(expr, item):
                r = re.compile(expr)
                return r.match(item) is not None

            self.__conn.connection.create_function("regexp", 2, sqlite_regexp)

        # Sync index
        if run_index:
            self.sync_index()

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
                sl = sl.order_by(order_by)
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
            cel = el.split("_")[0]
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

            elif not cel in self.__types:
                raise FilterException("attribute '%s' is not indexed" % el.split("_")[0])

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

    def sync_index(self):
        t0 = time()
        f = GOsaObjectFactory.getInstance()

        def resolve_children(dn):
            print " * found", dn
            res = {}

            children = f.getObjectChildren(dn)
            res = dict(res.items() + children.items())

            for chld in children.keys():
                res = dict(res.items() + resolve_children(chld).items())

            return res

        self.log.info("scanning for objects")
        res = resolve_children(u"ou=Vertrieb,dc=gonicus,dc=de")

        self.log.info("generating object index")
        to_be_indexed = ['uid', 'givenName', 'sn', 'mail']

        # Find new entries
        backend_objects = []
        for o, o_type in res.items():

            # Get object
            obj = f.getObject(o_type, o)

            # Check for index entry
            tmp = self.__conn.execute(select([self.__index.c._lastChanged], self.__index.c._uuid == obj.uuid))
            r = tmp.fetchone()
            tmp.close()

            # Gather index attributes
            attrs = {}
            for attr in to_be_indexed:
                if obj.hasattr(attr):
                    attrs[attr] = getattr(obj, attr)

            # Entry is not in the database
            if r == None:
                self.log.debug("creating object index for %s" % obj.uuid)
                ext = f.identifyObject(o)[1]
                self.insert(obj.uuid, o, _lastChanged=obj.modifyTimestamp, _type=o_type, _extensions=ext, **attrs)

            # Entry is in the database
            else:
                # OK: already there
                if obj.modifyTimestamp == r[0]:
                    self.log.debug("found up-to-date object index for %s" % obj.uuid)
                else:
                    self.log.debug("updating object index for %s" % obj.uuid)
                    ext = f.identifyObject(o)[1]
                    self.update(obj.uuid, _dn=o, _lastChanged=obj.modifyTimestamp, _type=o_type, _extension=ext, **attrs)

            backend_objects.append(obj.uuid)
            del obj

        # Remove old entries
        for entry in self.__conn.execute(select([self.__index.c._uuid])).fetchall():
            if entry[0] not in backend_objects:
                self.log.debug("removing object index for %s" % entry[0])
                self.remove(entry[0])

        t1 = time()
        self.log.info("processed %d entries in %ds" % (len(res), t1 - t0))
