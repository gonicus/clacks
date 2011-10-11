#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid
import datetime
import inspect
import sqlalchemy.sql
from sqlalchemy import create_engine
from sqlalchemy.sql import select, and_, or_, not_, func, asc
from sqlalchemy import Table, Column, Integer, Boolean, String, DateTime, Date, Unicode, MetaData, ColumnDefault


class FilterException(Exception):
    pass


class IndexEngine(object):

    __engine = None
    __conn = None
    __fixed = ['id', '_dn', '_uuid', '_lastChanged', '_extensions']

    def __init__(self, index_attrs):
        self.__engine = create_engine('sqlite:///index.db')

        # Table name
        idx = "index"

        # Load current database setup
        meta = MetaData(self.__engine)
        meta.reflect()

        reset = True
        if idx in meta.tables:
            current_attrs = set(index_attrs.keys())
            db_attrs = set([str(x)[len(idx) + 1:] for x in meta.tables[idx]._columns if not str(x)[len(idx) + 1:] in self.__fixed])

            if current_attrs == db_attrs:

                for attr in db_attrs:

                    # Check if we at least subclass the type we got from the
                    # database
                    s_type = type(getattr(meta.tables[idx]._columns, attr).type)
                    if (not issubclass(s_type, index_attrs[attr])):

                        # If that fails, maybe there's one other try in the
                        # class hierachy
                        superiours = inspect.getmro(index_attrs[attr])
                        if not (len(superiours) > 1 and issubclass(s_type, superiours[1])):
                            print "Looks like we've to refresh the object index:"
                            print "I-->", s_type
                            print "S-->", index_attrs[attr]
                            break
                else:
                    reset = False

        # Create schema for storing indexed attributes
        if reset:
            meta.drop_all()
            del meta

        metadata = MetaData()

        props = []
        for attr, typ in index_attrs.items():
            props.append(Column(attr, typ))

        self.__index = Table(idx, metadata,
            Column('_uuid', String, primary_key=True),
            Column('_dn', Unicode),
            Column('_lastChanged', DateTime),
            Column('_extensions', String),
            *props)

        metadata.create_all(self.__engine)

        # Establish the connection
        self.__conn = self.__engine.connect()

    def has_entry(self, euuid):
        tmp = self.__conn.execute(select([self.__index], self.__index.c._uuid == euuid))
        res = bool(tmp.fetchone())
        tmp.close()
        return res

    def insert(self, euuid, dn, **props):
        props['_uuid'] = euuid
        props['_dn']= dn

        # Convert all list types to Unicode strings
        props = dict([(attr, "|" + "|".join(key) + "|" if type(key) == list else key) for attr, key in props.items()])
        self.__conn.execute(self.__index.insert(), [props])

    def remove(self, euuid):
        self.__conn.execute(self.__index.delete().where(self.__index.c._uuid == euuid))

    def update(self, euuid, **props):
        # Convert all list types to Unicode strings
        props = dict([(attr, "|" + "|".join(key) + "|" if type(key) == list else key) for attr, key in props.items()])
        self.__conn.execute(self.__index.update().where(self.__index.c._uuid == euuid), [props])

    def count(self, fltr):
        return self.__conn.execute(
            select(
                [func.count(self.__index.c._uuid)],
                *self.__build_filter(fltr)
            )).fetchone()[0]

    def search(self, fltr, attrs=None, begin=None, end=None, order_by=None, descending=False):
        if not attrs:
            ats = [self.__index]
        else:
            ats = []
            for a in attrs:
                ats.append(getattr(self.__index.c, a))

        sl = select(ats, *self.__build_filter(fltr))

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

        return self.__conn.execute(sl).fetchall()

    def __build_filter(self, fltr):
        arg = []

        for el, value in fltr.items():

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

            else:
                arg.append(getattr(self.__index.c, el.split("_")[0]) == value)

        return arg

#       tmp = self.__conn.execute(select([self.__index], self.__index.c._uuid == euuid))
#       self.__conn.execute()
#---------------------------------------------------------------------

ie = IndexEngine({'givenName': Unicode, 'sn': Unicode, 'mail': String, 'uid': String, 'dob': Date})
#ie = IndexEngine({'givenName': Unicode, 'sn': Unicode, 'mail': String, 'uid': String, 'uidNumber': Integer})

u1 = str(uuid.uuid4())
ie.insert(u1, dn=u"cn=Cajus Pollmeier,ou=people,ou=Technik,dc=gonicus,dc=de", sn=u"Pollmeier", givenName=u"Cajus", uid="cajus", mail=['cajus@debian.org', 'cajus@naasa.net', 'pollmeier@gonicus.de'], _lastChanged=datetime.datetime.now())

print ie.has_entry(u1)
ie.update(u1, uid="lorenz")


#TODO: wildcard, maybe regex?
#TODO: filter for list elements -> |....|....|....|
#fltr = {}
fltr = {'uid': 'lorenz'}
#fltr = {'_and': {'uid': 'lorenz', 'givenName': u'Cajus', '_or': {'sn': u'ding', 'sn_2': u'dong', '_gt': ['dob', datetime.datetime.now()]}}}
#fltr = {'_and': {'uid': 'lorenz', 'givenName': u'Cajus', '_or': {'_in': {'sn': [u'ding', u'dong']}, '_gt': ['dob', datetime.datetime.now()]}}}
print "Count:", ie.count(fltr)
for e in ie.search(fltr, attrs=['sn', 'givenName', 'uid'], begin=0, end=10):
    print e

#ie.remove(u1)
#print ie.has_entry(u1)

#ie.refresh()
