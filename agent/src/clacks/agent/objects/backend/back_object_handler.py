# -*- coding: utf-8 -*-
import re 
from itertools import permutations
from logging import getLogger
from clacks.common import Environment
from clacks.agent.objects.backend import ObjectBackend, EntryNotFound, EntryNotUnique
from clacks.agent.objects.index import ObjectIndex
from clacks.common.components import PluginRegistry
from clacks.agent.objects import ObjectProxy


class NoSuchObject(Exception):
    pass


class NoBackendParametersFound(Exception):
    pass


class ObjectHandler(ObjectBackend):

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

            # Extract backend attrs
            mapping = ObjectHandler.extractBackAttrs(back_attrs)

            # Load related objects from the index and add the required attribute-values
            # as values for 'targetAttr'
            for targetAttr in mapping:
                result[targetAttr] = []
                foreignObject, foreignAttr, foreignMatchAttr, matchAttr = mapping[targetAttr]
                oi = PluginRegistry.getInstance("ObjectIndex")
                results = oi.xquery("collection('objects')/*/.[o:UUID = '%s']/o:Attributes/o:%s/string()" % (uuid, matchAttr))
                if results:
                    matchValue = results[0]
                    xq = "collection('objects')/o:%s/o:Attributes[o:%s = '%s']/o:%s/string()" % \
                            (foreignObject, foreignMatchAttr, matchValue, foreignAttr)
                    result[targetAttr]  = oi.xquery(xq);

        return result

    def extend(self, uuid, data, params, foreign_keys):
        return self.update(uuid, data, params)

    def retract(self, uuid, data, params):
        # Set values to an emtpy state, to enforce property removal
        for prop in data:
            data[prop]["value"] = []
        return self.update(uuid, data, params)

    def remove(self, uuid, data, params):
        return self.retract(uuid, data, params)

    def update(self, uuid, data, back_attrs):
        """
        Write back changes collected for foreign objects relations.

        E.g. If group memberships where modified from the user plugin
        we will forward the changes to the group objects.
        """

        # Extract usable information out og the backend attributes
        mapping = ObjectHandler.extractBackAttrs(back_attrs)
        oi = PluginRegistry.getInstance("ObjectIndex")

        # Ensure that we have a configuration for all attributes
        for attr in data.keys():
            if attr not in mapping:
                raise NoBackendParametersFound("attribute %s uses the ObjectHandler backend but there is no config for it!" % attr)
        #for targetAttr in mapping:
        #    if not targetAttr in data:
        #        raise NoBackendParametersFound("an attribute named %s is configured for the ObjectHandler backend but there" \
        #                                       " is no such attribute in the object" % targetAttr)

        # Walk through each mapped foreign-object-attribute
        for targetAttr in mapping:

            if not targetAttr in data:
                continue

            # Get the matching attribute for the current object
            foreignObject, foreignAttr, foreignMatchAttr, matchAttr = mapping[targetAttr]
            xq = "collection('objects')/*/.[o:UUID = '%s']/o:Attributes/o:%s/string()" % (uuid, matchAttr)
            res = oi.xquery(xq)
            if not res:
                raise Exception("source object could not be found" % targetAttr)
            matchValue = res[0]

            # Collect all objects that match the given value 
            allvalues = data[targetAttr]['orig'] + data[targetAttr]['value']
            object_mapping = {}
            for value in allvalues:
                xq = "collection('objects')/o:%s[o:Attributes/o:%s = '%s']/o:DN/string()" % \
                        (foreignObject, foreignAttr, value)
                res = oi.xquery(xq)
                if not res:
                    raise NoSuchObject("Could not find any '%s' with '%s=%s'!" % (foreignObject, foreignAttr, value))
                else:
                    object_mapping[value] = ObjectProxy(res[0])

            # Calculate value that have to be removed/added
            remove = list(set(data[targetAttr]['orig']) - set(data[targetAttr]['value']))
            add = list(set(data[targetAttr]['value']) - set(data[targetAttr]['orig']))

            # Remove ourselves from the foreign object
            for item in remove:
                if object_mapping[item]:
                    current_state = getattr(object_mapping[item], foreignMatchAttr)
                    new_state = [x for x in current_state if x != matchValue]
                    setattr(object_mapping[item], foreignMatchAttr, new_state)

            # Add ourselves to the foreign object
            for item in add:
                if object_mapping[item]:
                    current_state = getattr(object_mapping[item], foreignMatchAttr)
                    current_state.append(matchValue)
                    setattr(object_mapping[item], foreignMatchAttr, current_state)

            # Save changes
            for item in object_mapping:
                if object_mapping[item]:
                    object_mapping[item].commit()


    @staticmethod
    def extractBackAttrs(back_attrs):
        """
        Helper method to extract backendParameter infos
        """
        result = {}
        for targetAttr in back_attrs:
            result[targetAttr] = []
            res = re.match("^([^:]*):([^,]*),([^=]*)=(.*)", back_attrs[targetAttr])
            if res:
                result[targetAttr] = res.groups()
        return result

    def __init__(self):
        pass

    def __del__(self):
        self.lh.free_connection(self.con)

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

    def move_extension(self, uuid, new_base):
        pass

    def move(self, uuid, new_base):
        print "move", uuid
        return False

    def create(self, base, data, params, foreign_keys=None):
        print "create", base, data, params
        return None

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

