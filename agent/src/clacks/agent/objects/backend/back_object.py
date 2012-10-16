# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

import re
import itertools
from clacks.common.components import PluginRegistry
from clacks.common.error import ClacksErrorHandler as C
from clacks.agent.objects.backend import ObjectBackend
from clacks.agent.exceptions import EntryNotFound, BackendError
from clacks.agent.objects.index import ObjectIndex
from clacks.agent.objects import ObjectProxy


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
            mapping = self.extractBackAttrs(back_attrs)

            # Load related objects from the index and add the required attribute-values
            # as values for 'targetAttr'
            index = PluginRegistry.getInstance("ObjectIndex")
            for targetAttr in mapping:
                result[targetAttr] = []
                foreignObject, foreignAttr, foreignMatchAttr, matchAttr = mapping[targetAttr]
                results = index.search({'_uuid': uuid, matchAttr: {'$exists': True}}, {matchAttr: 1})
                if results.count():
                    matchValue = results[0][matchAttr][0]
                    xq = index.search({'_type': foreignObject, foreignMatchAttr: matchValue}, {foreignAttr: 1})
                    result[targetAttr] = list(itertools.chain.from_iterable([x[foreignAttr] for x in xq]))

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
        mapping = self.extractBackAttrs(back_attrs)
        index = PluginRegistry.getInstance("ObjectIndex")

        # Ensure that we have a configuration for all attributes
        for attr in data.keys():
            if attr not in mapping:
                raise BackendError(C.make_error("BACKEND_ATTRIBUTE_CONFIG_MISSING", attribute=attr))

        # Walk through each mapped foreign-object-attribute
        for targetAttr in mapping:

            if not targetAttr in data:
                continue

            # Get the matching attribute for the current object
            foreignObject, foreignAttr, foreignMatchAttr, matchAttr = mapping[targetAttr]
            res = index.search({'_uuid': uuid}, {matchAttr: 1})
            if not res.count():
                raise BackendError(C.make_error("SOURCE_OBJECT_NOT_FOUND", object=targetAttr))
            matchValue = res[0][matchAttr][0]

            # Collect all objects that match the given value
            allvalues = data[targetAttr]['orig'] + data[targetAttr]['value']
            object_mapping = {}
            for value in allvalues:
                res = index.search({'_type': foreignObject, foreignAttr: value}, {'dn': 1})
                if res.count() != 1:
                    raise EntryNotFound(C.make_error("NO_UNIQUE_ENTRY", object=foreignObject, attribute=foreignAttr, value=value))
                else:
                    object_mapping[value] = ObjectProxy(res[0]['dn'])

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
        raise BackendError(C.make_error("ID_GENERATION_FAILED"))

    def extractBackAttrs(self, attrs):
        result = {}
        for targetAttr in attrs:
            res = re.match("^([^:]*):([^,]*)(,([^=]*)=([^,]*))?", attrs[targetAttr])
            if res:
                result[targetAttr] = []
                result[targetAttr].append(res.groups()[0])
                result[targetAttr].append(res.groups()[1])
                result[targetAttr].append(res.groups()[3])
                result[targetAttr].append(res.groups()[4])

        return result
