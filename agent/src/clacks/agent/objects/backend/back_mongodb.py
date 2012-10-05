"""
This file is part of the clacks framework.

  http://clacks-project.org

Copyright:
  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de

License:
  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
  See the LICENSE file in the project's top-level directory for details.
"""

# -*- coding: utf-8 -*-
import re
import uuid
import ldap
import datetime
from logging import getLogger
from clacks.agent.objects.backend import ObjectBackend, DNGeneratorError, RDNNotSpecified, BackendError
from clacks.common import Environment
from clacks.common.utils import is_uuid


class MongoDB(ObjectBackend):

    data = None
    scope_map = None

    def __init__(self):
        # Initialize environment and logger
        self.env = Environment.getInstance()
        self.log = getLogger(__name__)

        # Create scope map
        self.scope_map = {}
        self.scope_map[ldap.SCOPE_SUBTREE] = "sub"
        self.scope_map[ldap.SCOPE_BASE] = "base"
        self.scope_map[ldap.SCOPE_ONELEVEL] = "one"

        # Get database collection
        db_name = self.env.config.get("mongodb.database", "storage")
        collection = self.env.config.get("mongodb.collection", "objects")
        db = self.env.get_mongo_db(db_name)
        self.db = db[collection]

        # Ensure basic index for the objects
        for index in ['dn', '_uuid', '_last_changed', '_type', '_parent_dn']:
            self.db.ensure_index(index)

    def load(self, item_uuid, info, back_attrs=None):
        """
        Load object properties for the given uuid
        """
        data = {}

        for entry in self.db.find({'_uuid': item_uuid}):
            del entry['_id']
            data.update(entry)

        return data

    def identify(self, object_dn, params, fixed_rdn=None):
        """
        Identify an object by dn
        """
        item_uuid = self.dn2uuid(object_dn)
        if not item_uuid:
            return False

        return self.identify_by_uuid(item_uuid, params)

    def identify_by_uuid(self, item_uuid, params):
        """
        Identify an object by uuid
        """
        return self.db.find_one({'_uuid': item_uuid, '_type': params['type']}) != None

    def retract(self, item_uuid, data, params):
        """
        Remove an object extension
        """
        self.db.remove({'_uuid': item_uuid, '_type': params['type']})

    def extend(self, item_uuid, data, params, foreign_keys):
        """
        Create an object extension
        """
        _data = {}
        for name in data:
            _data[name] = data[name]['value']

        _data['_uuid'] = item_uuid
        _data['_type'] = params['type']

        self.db.save(_data)

    def dn2uuid(self, object_dn):
        """
        Tries to identify the given dn in the json-database, if an
        entry with the given dn was found, its uuid is returned.
        """
        entry = self.db.find_one({'dn': object_dn}, {'_uuid': 1})
        if entry:
            return entry['_uuid']

        return None

    def uuid2dn(self, item_uuid):
        """
        Tries to find the given uuid in the backend and returnd the
        dn for the entry.
        """
        entry = self.db.find_one({'_uuid': item_uuid}, {'dn': 1})
        if entry:
            return entry['dn']

        return None

    def query(self, base, scope, params, fixed_rdn=None):
        """
        Queries the json-database for the given objects
        """

        # Build query: assemble
        if self.scope_map[scope] == "sub":
            query = {"dn": re.compile("^(.*,)?" + re.escape(base) + "$")}

        elif self.scope_map[scope] == "one":
            query = {"$or": [{"dn": base}, {"_parent_dn": base}]}

        else:
            query = {"dn": base}

        return [x['dn'] for x in self.db.find(query, {'dn': 1})]

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

        # Build the entry that will be written to the json-database
        _uuid = str(uuid.uuid1())
        obj = {
            'dn': object_dn,
            '_uuid': _uuid,
            '_type': params['type'],
            '_parent_dn': base,
            '_created': datetime.datetime.now(),
            '_last_changed': datetime.datetime.now()
        }

        # Move attributes
        for attr in data:
            obj[attr] = data[attr]['value']

        # Save object
        self.db.save(obj)

        # Return the uuid of the generated entry
        return _uuid

    def get_timestamps(self, object_dn):
        """
        Returns the create- and modify-timestamps for the given dn
        """
        entry = self.db.find_one({'dn': object_dn}, {'_created': 1, '_last_changed': 1})
        if entry:
            return (entry['_created'], entry['_last_changed'])

        return (None, None)

    def get_uniq_dn(self, rdns, base, data, FixedRDN):
        """
        Tries to find an unused dn for the given properties
        """

        # Check if there is still a free dn left
        dns = [e['dn'] for e in self.db.find({'dn': {'$exists': True}}, {'dn': 1})]
        for object_dn in self.build_dn_list(rdns, base, data, FixedRDN):
            if object_dn not in dns:
                return object_dn

        return None

    def remove(self, item_uuid, data, params):
        """
        Removes the entry with the given uuid from the database
        """
        return bool(self.db.remove({'_uuid': item_uuid}))

    def exists(self, misc):
        """
        Check whether the given uuid or dn exists
        """

        if is_uuid(misc):
            return bool(self.db.find_one({'_uuid': misc}, {'_uuid': 1}))
        else:
            return bool(self.db.find_one({'dn': misc}, {'_uuid': 1}))

    def is_uniq(self, attr, value, at_type):
        """
        Check whether the given attribute is not used yet.
        """

        return bool(self.db.find_one({attr: value}, {attr: 1}))

    def update(self, item_uuid, data, params):
        """
        Update the given entry (by uuid) with a new set of values.
        """
        changes = {}
        for item in data:
            changes[item] = data[item]['value']

        self.db.update({'_uuid': item_uuid}, {"$set": changes})
        return True

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
        entry = self.db.find_one({'_uuid': item_uuid}, {'dn': 1})
        if entry:
            dn = re.sub(re.escape(entry['_parent_dn']) + "$", new_base, entry['dn'])

            # Check if we can move the entry
            if self.exists(dn):
                raise BackendError("cannot move entry - the target DN '%s' already exists!" % dn)

            entry = dict(dn=dn, _parent_dn=new_base)
            self.db.update({'_uuid': item_uuid}, {"$set": entry})
            return True

        return False
