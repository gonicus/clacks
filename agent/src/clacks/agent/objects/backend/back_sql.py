"""
This class implements the SQL-Backend
"""

# -*- coding: utf-8 -*-
import re
import uuid
import ldap
import datetime
from clacks.agent.objects.backend import ObjectBackend
from json import loads, dumps
from logging import getLogger
from clacks.common import Environment
from itertools import permutations

from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, BLOB, DateTime
from sqlalchemy.sql import and_



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

        # Read storage path from config
        con_str = self.env.config.get("sql.backend_connection", None)
        if not con_str:
            raise Exception("no sql.backend_connection found in config file")

        # Create table definition
        self.engine = create_engine(con_str, echo=False)
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

        # Create table on demand
        self.metadata.create_all(self.engine)

    def load(self, item_uuid, info):
        """
        Load object properties for the given uuid
        """

        # Search for all entries with the given uuid and combine found attributes
        search = self.objects.select(self.objects.c.uuid==item_uuid).execute()
        data = {}
        for entry in search:

            # Convert json to python-dict and combine all attributes
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

        # Try to find an entry with the given uuid and type
        search = self.objects.select(and_(self.objects.c.uuid==item_uuid, self.objects.c.type == params['type'])).execute()
        entry = search.first()
        if entry:
            return True
        return False

    def retract(self, item_uuid, data, params):
        """
        Remove an object extension
        """

        # Remove the entry with the given uuid and type
        self.objects.delete().where(and_(self.objects.c.uuid==item_uuid, self.objects.c.type == params['type'])).execute()

    def extend(self, item_uuid, data, params, foreign_keys):
        """
        Create an object extension
        """

        # create a new database entry for the given  object-type (params['type'])
        attrs = {}
        for item in data:
            attrs[item] = data[item]['value']
        data = {}
        data['type'] = params['type']
        data['uuid'] = item_uuid
        data['attributes'] = dumps(attrs)

        # Insert the entry in the database
        self.objects.insert().execute(**data)

    def dn2uuid(self, object_dn):
        """
        Tries to identify the given dn in the json-database, if an
        entry with the given dn was found, its uuid is returned.
        """

        # Try to find an entry with the given dn and return its uuid on success
        search = self.objects.select(self.objects.c.dn==object_dn).execute()
        entry = search.first()
        if entry:
            return entry.uuid
        return None

    def uuid2dn(self, item_uuid):
        """
        Tries to find the given uuid in the backend and returnd the
        dn for the entry.
        """

        # Try to find an entry with the uuid and return its dn
        search = self.objects.select(and_(self.objects.c.dn != None, self.objects.c.uuid==item_uuid)).execute()
        entry = search.first()
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
            search = self.objects.select(self.objects.c.parentDN==base).execute()
            for item in search:
                found.append(item.dn)

        # For base searches the base has the dn has to match the requested base
        if self.scope_map[scope] == "base":
            search = self.objects.select(self.objects.c.dn==base).execute()
            for item in search:
                found.append(item.dn)

        # For sub-queries the requested-base has to be part parentDN
        if self.scope_map[scope] == "sub":
            search = self.objects.select(self.objects.c.parentDN.endswith(base)).execute()
            for item in search:
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
        fixed_rdn = params['FixedRDN'] if 'FixedRDN' in params else None

        # Get a unique dn for this entry, if there was no free dn left (None) throw an error
        object_dn = self.get_uniq_dn(rdns, base, data, fixed_rdn)
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

        # Insert the entry into the database
        self.objects.insert().execute(**obj)

        # Return the uuid of the generated entry
        return str_uuid

    def get_timestamps(self, object_dn):
        """
        Returns the create- and modify-timestamps for the given dn
        """
        search = self.objects.select(self.objects.c.dn==object_dn).execute().first()
        if search:
            ctime = search.createTimestamp
            mtime = search.modifyTimestamp
            return (ctime, mtime)
        return None, None


    def get_uniq_dn(self, rdns, base, data, fixed_rdn):
        """
        Tries to find an unused dn for the given properties
        """

        # Check if there is still a free dn left
        for object_dn in self.build_dn_list(rdns, base, data, fixed_rdn):
            if not self.objects.select(self.objects.c.dn == object_dn).execute().first():
                return object_dn

        return None

    def build_dn_list(self, rdns, base, data, fixed_rdn):
        """
        Build a list of possible DNs for the given properties
        """
        fix = rdns[0]
        var = rdns[1:] if len(rdns) > 1 else []
        dns = [fix]

        # Check if we've have to use a fixed RDN.
        if fixed_rdn:
            return(["%s,%s" % (fixed_rdn, base)])

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
            search = self.objects.select(self.objects.c.uuid==misc).execute().first()
        else:
            search = self.objects.select(self.objects.c.dn==misc).execute().first()
        return True if search else False

    def is_uniq(self, attr, value, at_type):
        """
        Check whether the given attribute is not used yet.
        """
        search = self.objects.select(getattr(self.objects.c, attr)==value).execute().first()
        return False if search else True

    def update(self, item_uuid, data, params):
        """
        Update the given entry (by uuid) with a new set of values.
        """

        # Try to find an entry with the given uuid and type (params['type']) and
        # update the objects attributes.
        o_type = params['type']
        entry = self.objects.select(and_(self.objects.c.uuid==item_uuid, self.objects.c.type==o_type)).execute().first()
        if entry:
            attrs = loads(entry.attributes)
            for item in data:
                attrs[item] = data[item]['value']

            # Update the database entry
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
