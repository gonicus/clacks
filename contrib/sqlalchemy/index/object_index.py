#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid
import datetime
import sqlalchemy.sql
from sqlalchemy import create_engine
from sqlalchemy.sql import select, and_, or_, not_, func
from sqlalchemy import Table, Column, Integer, Boolean, String, DateTime, Date, Unicode, MetaData, ColumnDefault


class IndexEngine(object):

    __engine = None
    __conn = None

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
            db_attrs = set([str(x)[len(idx) + 1:] for x in meta.tables[idx]._columns if not str(x)[len(idx) + 1:] in ['id', '_dn', '_uuid', '_lastChanged', ]])

            if current_attrs == db_attrs:

                for attr in db_attrs:
                    if (getattr(meta.tables[idx]._columns, attr).type) != index_attrs[attr]:
                        #TODO: this is fuzzy because VARCHAR != STRING, etc.
                        print "FIXME"
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

        #if begin and end:
        #    return self.__conn.execute(select(ats, *self.__build_filter(fltr))).fetchall()

        return self.__conn.execute(select(ats, *self.__build_filter(fltr))).fetchall()

    def __build_filter(self, fltr):
        arg = []

        for el, value in fltr.items():

            if el in ["_and", "_or", "_not"]:
                if type(value) == dict:
                    v = getattr(sqlalchemy.sql, el[1:] + "_")(*self.__build_filter(value))
                    arg.append(v)
                else:
                    raise Exception("bad filter")

            elif el in ["_gt", "_lt", "_ge", "_le"]:
                if len(value) != 2:
                    raise Exception("bad filter")

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
                    raise Exception("bad filter")

            elif el == "_in":
                if len(value) != 1:
                    raise Exception("bad filter")

                k, v = value.items()[0]
                if type(v) != list:
                    raise Exception("bad filter")

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


fltr = {'uid': 'lorenz'}
#fltr = {'_and': {'uid': 'lorenz', 'givenName': u'Cajus', '_or': {'sn': u'ding', 'sn_2': u'dong', '_gt': ['dob', datetime.datetime.now()]}}}
#fltr = {'_and': {'uid': 'lorenz', 'givenName': u'Cajus', '_or': {'_in': {'sn': [u'ding', u'dong']}, '_gt': ['dob', datetime.datetime.now()]}}}
print "Count:", ie.count(fltr)
print ie.search(fltr, attrs=['sn', 'givenName', 'uid'], begin=0, end=10)

ie.remove(u1)
print ie.has_entry(u1)

#ie.refresh()
