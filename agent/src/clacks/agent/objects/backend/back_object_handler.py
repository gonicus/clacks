# -*- coding: utf-8 -*-
from itertools import permutations
from logging import getLogger
from clacks.common import Environment
from clacks.agent.objects.backend import ObjectBackend, EntryNotFound, EntryNotUnique
from clacks.agent.objects.index import ObjectIndex
from clacks.common.components import PluginRegistry


class ObjectHandler(ObjectBackend):

    def __init__(self):
        pass

    def __del__(self):
        self.lh.free_connection(self.con)

    def load(self, uuid, info, back_attrs=None):
        """
        Load attributes for the given object-uuid.

        This method resolves relations between objects, e.g. user-group-memberships.
        For example, to have an attribute called groupMembership for 'User' objects
        we've to collect all 'Group->cn' attributes where 'Group->memberUid' includes
        the 'User->uid' attribute.

        Example:
            User->uid = 'herbert'

            Group->cn = "admins"
            Group->memberUid = ['klaus', 'herbert', '...']

            Group->cn = "support"
            Group->memberUid = ['manfred', 'herbert']

            User->groupMembership = ['admins', 'support', '..,', 'and', 'maybe', 'others']

        Due to the fact that not all groups may already be loaded during indexing, 
        we have to postpone this process after the index-process has finished and 
        all objects were inserted to the index.

        Take a look at the 'ObjectIndex' and its static variable 'first_run' for details.

        """
        result = {}
        if ObjectIndex.first_run:
            ObjectIndex.to_be_updated.append(uuid)
        else:
            for targetAttr in back_attrs:
                result[targetAttr] = []
                import re 
                res = re.match("^([^:]*):([^,]*),([^=]*)=(.*)", back_attrs[targetAttr])
                if res:
                    #PosixGroup:cn,memberUid=uid
                    foreignObject, foreignAttr, foreignMatchAttr, matchAttr = res.groups()
                    oi = PluginRegistry.getInstance("ObjectIndex")
                    results = oi.xquery("collection('objects')/*/.[o:UUID = '%s']/o:Attributes/o:%s/string()" % (uuid, matchAttr))
                    if results:
                        matchValue = results[0]

                        xq = "collection('objects')/o:%s/o:Attributes[o:%s = '%s']/o:%s/string()" % \
                                (foreignObject, foreignMatchAttr, matchValue, foreignAttr)
                        results = oi.xquery(xq);
                        if results:
                            result[targetAttr].append(results[0])

        print result
        return result

    def identify_by_uuid(self, uuid, params):
        return False

    def identify(self, dn, params, fixed_rdn=None):
        return False

    def query(self, base, scope, params, fixed_rdn=None):
        print "query", base, scope, params, fixed_rdn
        return []

    def exists(self, misc):
        print "exists", misc
        return False

    def remove(self, uuid):
        print "remove", uuid
        return False

    def retract(self, uuid, data, params):
        print "retract", uuid, data, params
        pass

    def extend(self, uuid, data, params, foreign_keys):
        print "extend", uuid, data, params
        return False

    def move_extension(self, uuid, new_base):
        pass

    def move(self, uuid, new_base):
        print "move", uuid
        return False

    def create(self, base, data, params, foreign_keys=None):
        print "create", base, data, params
        return None

    def update(self, uuid, data, params):
        print "update", uuid
        return False

    def uuid2dn(self, uuid):
        return None

    def dn2uuid(self, dn):
        return None

    def get_timestamps(self, dn):
        return (None, None)

    def get_uniq_dn(self, rdns, base, data, FixedRDN):
        return None

    def is_uniq(self, attr, value, at_type):
        return False

    def get_next_id(self, attr):
        raise EntryNotFound("cannot generate IDs")

