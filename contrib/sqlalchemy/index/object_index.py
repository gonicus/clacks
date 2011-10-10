#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid
import datetime
from sqlalchemy import create_engine
from sqlalchemy.sql import select, and_, or_, not_
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
        print props
        self.__conn.execute(self.__index.update().where(self.__index.c._uuid == euuid), [props])

#---------------------------------------------------------------------

ie = IndexEngine({'givenName': Unicode, 'sn': Unicode, 'mail': String, 'uid': String})
#ie = IndexEngine({'givenName': Unicode, 'sn': Unicode, 'mail': String, 'uid': String, 'uidNumber': Integer})

#ie.count(filter)
#ie.search(filter, begin, end)

u1 = str(uuid.uuid4())
ie.insert(u1, dn=u"cn=Cajus Pollmeier,ou=people,ou=Technik,dc=gonicus,dc=de", sn=u"Pollmeier", givenName=u"Cajus", uid="cajus", mail=['cajus@debian.org', 'cajus@naasa.net', 'pollmeier@gonicus.de'], _lastChanged=datetime.datetime.now())
print ie.has_entry(u1)
ie.update(u1, uid="lorenz")
ie.remove(u1)
print ie.has_entry(u1)

#ie.refresh()
