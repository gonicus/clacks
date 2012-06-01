# -*- coding: utf-8 -*-
from clacks.agent.objects.types import AttributeType
from json import loads, dumps

class AclRole(AttributeType):
    """
    This is a special object-attribute-type for AclAction.

    This class can convert acl-actions into an UnicodeString and vice versa.
    """

    __alias__ = "AclRole"

    def values_match(self, value1, value2):
        """
        Checks whether the given values are equal
        """
        return(str(value1) == str(value2))

    def is_valid_value(self, value):
        """
        Checks if the given value for AclAction is valid.
        """
        if len(value):
            for entry in value:
                if type(entry) != dict:
                    return False
        return True

    def _convert_to_unicodestring(self, value):
        """
        This method is a converter used when values gets read from or written to the backend.
        Converts the 'AclAction' object-type into a 'UnicodeString'-object.
        """

        if len(value):
            res = []
            for entry in value:
                item = "%(scope)s\n%(priority)s\n" % (entry)
                if not "members" in entry:
                    entry["members"] = []
                item += ",".join(entry["members"])

                for action in entry["actions"]:
                    item += "\n%(topic)s:%(acl)s:%(options)s" % action
                res.append(item)
            return res
        return(value)

    def _convert_from_string(self, value):
        """
        See _convert_from_unicodestring
        """
        return self._convert_from_unicodestring(value)

    def _convert_from_unicodestring(self, value):
        """
        This method is a converter used when values were read from or written to the backend.
        Converts an 'UnicodeString' string into a 'AclAction'-object.
        """
        if len(value):

            new_value = []
            for item in value:
                data = item.split("\n")
                scope, priority, members_str = data[:3]
                members = members_str.split(",")
                actions = data[3::]

                if "" in members:
                    members.remove("")

                new_entry = {}
                new_entry['scope'] = scope
                new_entry['priority'] = priority
                new_entry['members'] = members
                new_entry['actions'] = []
                new_value.append(new_entry)

                for action in actions:
                    if not action:
                        continue

                    topic, acl, options = action.split(":")
                    new_entry['actions'].append({"topic": topic, "acl": acl, "options": options})

        return(new_value)
