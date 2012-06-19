"""
This class implements the SQL-Backend
"""

# -*- coding: utf-8 -*-
import os
import re
import uuid
import datetime
from clacks.agent.objects.backend import ObjectBackend
from json import loads, dumps
from logging import getLogger
from clacks.common import Environment
from itertools import permutations
import ldap

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, BLOB, DateTime
from sqlalchemy.sql import select, and_



class RDNNotSpecified(Exception):
    """
    Exception thrown for missing rdn property in object definitions
    """
    pass


class DNGeneratorError(Exception):
    """
    Exception thrown for dn generation errors
    """
    pass


class BackendError(Exception):
    """
    Exception thrown for unknown objects
    """
    pass


class SQL(ObjectBackend):

    data = None
    scope_map = None
    engine = None
    objects = None

    def __init__(self):

        # Initialize environment and logger
        self.env = Environment.getInstance()
        self.log = getLogger(__name__)

        # Create scope map
        self.scope_map = {}
        self.scope_map[ldap.SCOPE_SUBTREE] = "sub"
        self.scope_map[ldap.SCOPE_BASE] = "base"
        self.scope_map[ldap.SCOPE_ONELEVEL] = "one"
        self.connect()

    def connect(self):
        self.engine = create_engine('sqlite:////tmp/file.db', echo=False)
        self.metadata = MetaData()
        self.metadata.bind = self.engine

        self.objects = Table('objects', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('dn', String(255)),
                Column('uuid', String(36)),
                Column('createTimestamp', DateTime),
                Column('parentDN', String(255)),
                Column('type', String(64)),
                Column('modifyTimestamp', DateTime),
                Column('attributes', BLOB())
                )
        self.metadata.create_all(self.engine)


    def load(self, item_uuid, info):
        """
        Load object properties for the given uuid
        """
        s = self.objects.select(self.objects.c.uuid==item_uuid).execute()
        data = {}
        for entry in s:
            attrs = loads(entry.attributes)
            for attrname in attrs:
                data[attrname] = attrs[attrname]
        return data

    def identify(self, object_dn, params, fixed_rdn=None):
        """
        Identify an object by dn
        """
        return self.identify_by_uuid(self.dn2uuid(object_dn), params)

    def identify_by_uuid(self, item_uuid, params):
        """
        Identify an object by uuid
        """
        s = self.objects.select(and_(self.objects.c.uuid==item_uuid, self.objects.c.type == params['type'])).execute()
        entry = s.first()
        if entry:
            return True
        return False

    def retract(self, item_uuid, data, params):
        """
        Remove an object extension
        """
        self.objects.delete().where(and_(self.objects.c.uuid==item_uuid, self.objects.c.type == params['type'])).execute()

    def extend(self, item_uuid, data, params, foreign_keys):
        """
        Create an object extension
        """
        attrs = {}
        for item in data:
            attrs[item] = data[item]['value']
        data= {}
        data['type']=params['type']
        data['uuid']=item_uuid
        data['attributes']=dumps(attrs)
        self.objects.insert().execute(**data)

    def dn2uuid(self, object_dn):
        """
        Tries to identify the given dn in the json-database, if an
        entry with the given dn was found, its uuid is returned.
        """
        s = self.objects.select(self.objects.c.dn==object_dn).execute()
        entry = s.first()
        if entry:
            return entry.uuid
        return None

    def uuid2dn(self, item_uuid):
        """
        Tries to find the given uuid in the backend and returnd the
        dn for the entry.
        """
        s = self.objects.select(self.objects.c.uuid==item_uuid).execute()
        entry = s.first()
        if entry:
            return entry.dn
        return None

    def query(self, base, scope, params, fixed_rdn=None):
        """
        Queries the json-database for the given objects
        """

        # Search for the given criteria.
        # For one-level scope the parentDN must be equal with the reqeusted base.
        found = []
        if self.scope_map[scope] == "one":
            s = self.objects.select(self.objects.c.parentDN==base).execute()
            for item in s:
                found.append(item.dn)

        # For base searches the base has the dn has to match the requested base
        if self.scope_map[scope] == "base":
            s = self.objects.select(self.objects.c.dn==base).execute()
            for item in s:
                found.append(item.dn)

        # For sub-queries the requested-base has to be part parentDN
        if self.scope_map[scope] == "sub":
            s = self.objects.select(self.objects.c.parentDN.endswith(base)).execute()
            for item in s:
                found.append(item.dn)
        return found

    def create(self, base, data, params, foreign_keys=None):
        """
        Creates a new database entry
        """

        # All entries require a naming attribute, if it's not available we cannot generate a dn for the entry
        if not 'rdn' in params:
            raise RDNNotSpecified("there is no 'RDN' backend parameter specified")

        # Split given rdn-attributes into a list.
        rdns = [d.strip() for d in params['rdn'].split(",")]

        # Get FixedRDN attribute
        FixedRDN = params['FixedRDN'] if 'FixedRDN' in params else None

        # Get a unique dn for this entry, if there was no free dn left (None) throw an error
        object_dn = self.get_uniq_dn(rdns, base, data, FixedRDN)
        if not object_dn:
            raise DNGeneratorError("no unique DN available on '%s' using: %s" % (base, ",".join(rdns)))
        object_dn = object_dn.encode('utf-8')

        # Build the entry that will be written to the json-database
        str_uuid = str(uuid.uuid1())
        obj = {}
        obj['dn'] = object_dn
        obj['uuid'] = str_uuid
        obj['type'] = params['type']
        obj['parentDN'] = base
        obj['modifyTimestamp'] = obj['createTimestamp'] = datetime.datetime.now()
        attrs = {}
        for attr in data:
            attrs[attr] = data[attr]['value']
        obj['attributes'] = dumps(attrs)

        self.objects.insert().execute(**obj)

        # Return the uuid of the generated entry
        return str_uuid

    def get_timestamps(self, object_dn):
        """
        Returns the create- and modify-timestamps for the given dn
        """
        s = self.objects.select(self.objects.c.dn==object_dn).execute().first()
        if s:
            ctime = s.createTimestamp
            mtime = s.modifyTimestamp
            return (ctime, mtime)
        return None, None


    def get_uniq_dn(self, rdns, base, data, FixedRDN):
        """
        Tries to find an unused dn for the given properties
        """

        # Check if there is still a free dn left
        for object_dn in self.build_dn_list(rdns, base, data, FixedRDN):
            if not self.objects.select(self.objects.c.dn == object_dn).execute().first():
                return object_dn

        return None

    def build_dn_list(self, rdns, base, data, FixedRDN):
        """
        Build a list of possible DNs for the given properties
        """
        fix = rdns[0]
        var = rdns[1:] if len(rdns) > 1 else []
        dns = [fix]

        # Check if we've have to use a fixed RDN.
        if FixedRDN:
            return(["%s,%s" % (FixedRDN, base)])

        # Bail out if fix part is not in data
        if not fix in data:
            raise DNGeneratorError("fix attribute '%s' is not in the entry" % fix)

        # Append possible variations of RDN attributes
        if var:
            for rdn in permutations(var + [None] * (len(var) - 1), len(var)):
                dns.append("%s,%s" % (fix, ",".join(filter(lambda x: x and x in data and data[x], list(rdn)))))
        dns = list(set(dns))

        # Assemble DN of RDN combinations
        dn_list = []
        for t in [tuple(d.split(",")) for d in dns]:
            ndn = []
            for k in t:
                ndn.append("%s=%s" % (k, ldap.dn.escape_dn_chars(data[k]['value'][0])))
            dn_list.append("+".join(ndn) + "," + base)

        return sorted(dn_list, key=len)

    def remove(self, item_uuid, recursive=False):
        """
        Removes the entry with the given uuid from the database
        """
        self.objects.delete().where(self.objects.c.uuid==item_uuid).execute()

    def exists(self, misc):
        """
        Check whether the given uuid or dn exists
        """

        if self.is_uuid(misc):
            s = self.objects.select(self.objects.c.uuid==misc).execute().first()
        else:
            s = self.objects.select(self.objects.c.dn==misc).execute().first()
        return True if res else False

    def is_uniq(self, attr, value, at_type):
        """
        Check whether the given attribute is not used yet.
        """
        s = self.objects.select(getattr(self.objects.c, attr)==value).execute().first()
        return False if res else True

    def update(self, item_uuid, data, params):
        """
        Update the given entry (by uuid) with a new set of values.
        """
        o_type = params['type']
        entry = self.objects.select(and_(self.objects.c.uuid==item_uuid, self.objects.c.type==o_type)).execute().first()
        if entry:
            attrs = loads(entry.attributes)
            for item in data:
                attrs[item] = data[item]['value']
            self.objects.update().where(self.objects.c.uuid==item_uuid).values(modifyTimestamp=datetime.datetime.now(), attributes=dumps(attrs)).execute()
            return True
        return False

    def move_extension(self, item_uuid, new_base):
        """
        Moves the extension to a new base
        """
        # Nothing to do here.
        return True

    def move(self, item_uuid, new_base):
        """
        Moves an entry to antoher base
        """
        entry = self.objects.select(self.objects.c.uuid==item_uuid).execute().first()
        if entry:
            dn = re.sub(re.escape(entry['parentDN'])+"$", new_base, entry['dn'])
            parentDN = new_base
            if self.exists(dn):
                raise BackendError("cannot move entry, the target DN '%s' already exists!" % dn)

            self.objects.update().where(self.objects.c.uuid==item_uuid).values(modifyTimestamp=datetime.datetime.now(), dn=dn, parentDN=parentDN).execute()
            return True
        return False
