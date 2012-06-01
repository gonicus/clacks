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
                for action in entry["actions"]:
                    item += "\n%(topic)s:%(acl)s:" % action
                    if "options" in action:
                        item += dumps(action["options"])

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

            # Convert each acl-role entry into a usable dict
            # The result will look like this
            new_value = []
            for item in value:
                data = item.split("\n")
                scope, priority, members_str = data[:3]
                actions = data[3::]

                new_entry = {}
                new_entry['scope'] = scope
                new_entry['priority'] = priority
                new_entry['actions'] = []
                new_value.append(new_entry)

                # Append actions, but skip processing empty lines
                for action in actions:
                    if not action:
                        continue

                    topic, acl, options_json = action.split(":", 2)
                    if options_json:
                        options = loads(options_json)
                    else:
                        options = {}

                    new_entry['actions'].append({"topic": topic, "acl": acl, "options": options})

        return(new_value)
