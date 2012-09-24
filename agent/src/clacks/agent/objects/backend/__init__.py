# -*- coding: utf-8 -*-
__import__('pkg_resources').declare_namespace(__name__)
import re
import ldap
from itertools import permutations


class EntryNotUnique(Exception):
    pass


class EntryNotFound(Exception):
    pass


class DNGeneratorError(Exception):
    """
    Exception thrown for dn generation errors
    """
    pass


class RDNNotSpecified(Exception):
    """
    Exception thrown for missing rdn property in object definitions
    """
    pass


class BackendError(Exception):
    """
    Exception thrown for unknown objects
    """
    pass


class ObjectBackend(object):
    _is_uuid = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')

    def dn2uuid(self, dn):
        """
        Convert DN to uuid.
        """
        raise NotImplementedError("object backend is not capable of mapping DN to UUID")

    def uuid2dn(self, uuid):
        """
        Convert uuid to DN.
        """
        raise NotImplementedError("object backend is not capable of mapping UUID to DN")

    def get_timestamps(self, dn):
        """
        Return a tuple (createdTimestamp, modifyTimestamp)
        """
        return (None, None)

    def load(self, uuid, keys, back_attrs=None):
        """
        Load given keys from entry with uuid.
        """
        raise NotImplementedError("object backend is missing load()")

    def move(self, uuid, new_base):
        """
        Move object to new base.
        """
        raise NotImplementedError("object backend is not capable of moving objects")

    def move_extension(self, uuid, new_base):
        """
        Notify extension that it is on another base now.
        """
        raise NotImplementedError("object backend is not capable of moving extensions")

    def create(self, dn, data, params):
        """
        Create a new base object entry with the given DN.
        """
        raise NotImplementedError("object backend is not capable of creating base objects")

    def extend(self, uuid, data, params, foreign_keys):
        """
        Create an extension to a base object with the given UUID.
        """
        raise NotImplementedError("object backend is not capable of creating object extensions")

    def update(self, uuid, data, params):
        """
        Update a base entry or an extension with the given UUID.
        """
        raise NotImplementedError("object backend is missing update()")

    def exists(self, misc):
        """
        Check if an object with the given UUID or DN exists.
        """
        raise NotImplementedError("object backend is missing exists()")

    def remove(self, uuid, data, params):
        """
        Remove base object specified by UUID.
        """
        raise NotImplementedError("object backend is missing remove()")

    def retract(self, uuid, data, params):
        """
        Retract extension from base object specified by UUID.
        """
        raise NotImplementedError("object backend is missing retract()")

    def is_uuid(self, uuid):
        return bool(self._is_uuid.match(uuid))

    def is_uniq(self, attr, value):
        """
        Check if the given attribute is unique.
        """
        raise NotImplementedError("object backend is missing is_uniq()")

    def identify(self, dn, params, fixed_rdn=None):
        raise NotImplementedError("object backend is missing identify()")

    def identify_by_uuid(self, dn, params):
        raise NotImplementedError("object backend is missing identify_by_uuid()")

    def query(self, base, scope, params, fixed_rdn=None):
        raise NotImplementedError("object backend is missing query()")

    def get_next_id(self, attr):
        raise NotImplementedError("object backend is missing get_next_id()")

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
