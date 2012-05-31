"""
This class implements the Json-Backend which is capable of storing clacks-objects.
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


class JsonBackendError(Exception):
    """
    Exception thrown for unknown objects
    """
    pass


class JSON(ObjectBackend):

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

        # Read storage path from config
        self._file_path = self.env.config.get("json.database_file", None)
        if not self._file_path:
            raise Exception("no json.database_file found in config file")

        # Create a json file on demand
        if not os.path.exists(self._file_path):
            open(self._file_path, "w").write(dumps({}))

    def __load(self):
        """
        Loads the json file and returns a object
        """
        return loads(open(self._file_path).read())

    def __save(self, json):
        """
        Saves back the given object to the json file.
        """
        open(self._file_path, "w").write(dumps(json, indent=2))

    def load(self, uuid, info):
        """
        Load object properties for the given uuid
        """
        json = self.__load()
        data = {}
        if uuid in json:
            data = dict(data.items() + json[uuid].items())
            return data
        return {}

    def identify(self, object_dn, params, fixed_rdn=None):
        """
        Identify an object by dn
        """
        uuid = self.dn2uuid(object_dn)
        if not uuid:
            return False

        res =  self.identify_by_uuid(uuid, params)
        return res

    def identify_by_uuid(self, uuid, params):
        """
        Identify an object by uuid
        """
        json = self.__load()
        if uuid in json and params['type'] == json[uuid]['type']:
            return True
        return False

    def retract(self, uuid, data, params):
        """
        Remove an object extension
        """
        json = self.__load()
        if uuid in json:
            del(json[uuid])
        self.__save(json)

    def extend(self, uuid, data, params, foreign_keys):
        """
        Create an object extension
        """
        json = self.__load()
        json[uuid] = {'type': params['type']}
        for item in data:
            json[uuid][item] = data[item]['value']
        self.__save(json)

    def dn2uuid(self, object_dn):
        """
        Tries to identify the given dn in the json-database, if an
        entry with the given dn was found, its uuid is returned.
        """
        json = self.__load()
        for item in json:
            if 'dn' in json[item] and object_dn == json[item]['dn']:
                return item
        return None

    def uuid2dn(self, uuid):
        """
        Tries to find the given uuid in the backend and returnd the
        dn for the entry.
        """
        json = self.__load()
        if uuid in json and "dn" in json[uuid]:
            return json[uuid]["dn"]
        return None

    def query(self, base, scope, params, fixed_rdn=None):
        """
        Queries the json-database for the given objects
        """

        # Load json database
        json = self.__load()

        # Search for the given criteria.
        # For one-level scope the parentDN must be equal with the reqeusted base.
        found = []
        if self.scope_map[scope] == "one":
            for item in json:
                if json[item]['parentDN'] == base:
                    found.append(json[item]['dn'])

        # For base searches the base has the dn has to match the requested base
        if self.scope_map[scope] == "base":
            for item in json:
                if json[item]['dn'] == base:
                    found.append(json[item]['dn'])

        # For sub-queries the requested-base has to be part parentDN
        if self.scope_map[scope] == "sub":
            for item in json:
                if re.match(re.escape(json[item]['parentDN']) + "$", base):
                    found.append(json[item]['dn'])
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
        json = self.__load()
        str_uuid = str(uuid.uuid1())
        obj = {}
        obj['dn'] = object_dn
        obj['type'] = params['type']
        obj['parentDN'] = base
        obj['modifyTimestamp'] = obj['createTimestamp'] = datetime.datetime.now().isoformat()
        for attr in data:
            obj[attr] = data[attr]['value']

        # Append the entry to the databse and save the changes
        json[str_uuid] = obj
        self.__save(json)

        # Return the uuid of the generated entry
        return str_uuid

    def get_timestamps(self, object_dn):
        """
        Returns the create- and modify-timestamps for the given dn
        """
        json = self.__load()
        uuid = self.dn2uuid(object_dn)
        if uuid:
            if 'createTimestamp' in json[uuid]:
                ctime = datetime.datetime.strptime(json[uuid]['createTimestamp'], "%Y-%m-%dT%H:%M:%S.%f")
            if 'modifyTimestamp' in json[uuid]:
                mtime = datetime.datetime.strptime(json[uuid]['modifyTimestamp'], "%Y-%m-%dT%H:%M:%S.%f")
        return (ctime, mtime)


    def get_uniq_dn(self, rdns, base, data, FixedRDN):
        """
        Tries to find an unused dn for the given properties
        """

        # Get all DNs
        json = self.__load()
        dns = []
        for item in json:
            if "dn" in json[item]:
                dns.append(json[item]["dn"])

        # Check if there is still a free dn left
        for object_dn in self.build_dn_list(rdns, base, data, FixedRDN):
            if object_dn not in dns:
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

    def remove(self, uuid, recursive=False):
        """
        Removes the entry with the given uuid from the database
        """
        json = self.__load()
        if uuid in json:
            del(json[uuid])
            self.__save(json)
            return True
        return False

    def exists(self, misc):
        """
        Check whether the given uuid or dn exists
        """
        json = self.__load()
        if self.is_uuid(misc):
            return uuid in json
        else:
            for item in json:
                if "dn" in json[item] and json[item]["dn"] == misc:
                    return True

        return False

    def is_uniq(self, attr, value, at_type):
        """
        Check whether the given attribute is not used yet.
        """
        json = self.__load()
        for item in json:
            if attr in json[item] and json[item][attr] == value:
                return False
        return True

    def update(self, uuid, data):
        """
        Update the given entry (by uuid) with a new set of values.
        """
        json = self.__load()
        if uuid in json:
            for item in data:
                json[uuid][item] = data[item]['value']
            self.__save(json)
            return True
        return False

    def move_extension(self, uuid, new_base):
        """
        Moves the extension to a new base
        """
        # Nothing to do here.
        return True

    def move(self, uuid, new_base):
        json = self.__load()
        if uuid in json:

            # Update the source entry
            entry = json[uuid]
            entry['dn'] = re.sub(re.escape(entry['parentDN'])+"$", new_base, entry['dn'])
            entry['parentDN'] = new_base

            # Check if we can move the entry
            if self.exists(entry['dn']):
                raise JsonBackendError("cannot move entry, the target DN '%s' already exists!" % entry['dn'])

            # Save the changes
            json[uuid] = entry
            self.__save(json)
            return True
        return False
