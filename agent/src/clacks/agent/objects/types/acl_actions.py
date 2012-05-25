# -*- coding: utf-8 -*-
from clacks.agent.objects.types import AttributeType


class AclAction(AttributeType):
    """
    This is a special object-attribute-type for AclAction.

    This class can convert acl-actions into an UnicodeString and vice versa.
    """

    __alias__ = "AclAction"

    def values_match(self, value1, value2):
        return(str(value1) == str(value2))

    def is_valid_value(self, value):
        if len(value):
            for entry in value:
                if type(entry) != dict:
                    return False
                if not "topic" in entry or "acl" not in entry:
                    return False
                if type(entry["topic"]) not in  [str, unicode]:
                    return False
                if type(entry["acl"]) not in [str, unicode]:
                    print "4"
                    return False
                if "options" in entry and type(entry["options"]) != dict:
                    print "5"
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
                res.append(entry["topic"] + ":" + entry["acl"])
            return res
        return(value)

    def _convert_from_string(self, value):
        return self._convert_from_unicodestring(value)

    def _convert_from_unicodestring(self, value):
        """
        This method is a converter used when values gets read from or written to the backend.
        Converts an 'UnicodeString' string into a 'AclAction'-object.
        """
        if len(value):
            res = []
            for entry in value:
                print entry
                data = entry.split(":")
                item = {}
                item["topic"] = data[0]
                item["acl"] = data[1]
                item["options"] = {}
                res.append(item)
            return res
        return(value)
