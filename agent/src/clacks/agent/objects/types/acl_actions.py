# -*- coding: utf-8 -*-
from clacks.agent.objects.types import AttributeType
from json import loads, dumps

class AclAction(AttributeType):
    """
    This is a special object-attribute-type for AclAction.

    This class can convert acl-actions into an UnicodeString and vice versa.
    """

    __alias__ = "AclAction"

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

                # This object has to be of type dict
                if type(entry) != dict:
                    return False

                # We can either have a reference to a role or define permissions
                # manually by specifying 'topic', 'acl' (and 'options')
                if "rolename" in entry and len(entry) == 1:
                    return True

                # If acls were specified manually than check for the required
                # parameters
                if not "topic" in entry or "acl" not in entry:
                    return False
                if type(entry["topic"]) not in  [str, unicode]:
                    return False
                if type(entry["acl"]) not in [str, unicode]:
                    return False
                if "options" in entry and type(entry["options"]) != dict:
                    return False

        return True

    def _convert_to_unicodestring(self, value):
        """
        This method is a converter used when values gets read from or written to the backend.
        Converts the 'AclAction' object-type into a 'UnicodeString'-object.
        """

        if len(value):

            # Walk through given Acl-objects and transform them into unicode
            res = []
            for entry in value:

                # This acl-object uses a role instead of defining acls itself.
                if "rolename" in entry:
                    str_acl = "%s" % (entry["rolename"])

                else:

                    # This acl-object defines its own acls.
                    # it will look like: <topic>:<acl>:<options>
                    #              e.g.: ^net\.example\..*$:rwcdsex:user=horst,maildomain=gonicus.de
                    str_acl = entry["topic"] + ":" + entry["acl"]
                    opts = []
                    if "options" in entry:
                        for key, val in entry['options'].items():
                            opts.append("%s=%s" % (key, val))

                        if opts:
                            str_acl += ":" + ",".join(opts)
                # Append the generated result string
                res.append(str_acl)
            return res
        return(value)

    def _convert_from_string(self, value):
        """
        See _convert_from_unicodestring
        """
        return self._convert_from_unicodestring(value)

    def _convert_from_unicodestring(self, value):
        """
        This method is a converter used when values gets read from or written to the backend.
        Converts an 'UnicodeString' string into a 'AclAction'-object.
        """
        if len(value):

            # Go through all attribute values and extract the informations
            # An acl-entry looks like:  <topic>:<acl>:<options>
            #         and a role like:  <rolename>
            res = []
            for entry in value:

                # Split the given string by ':'
                item = {}
                data = entry.split(":")

                # This acl uses a role
                if len(data) == 1:
                    item["rolename"] = data[0]
                else:

                    # This acl defines its own acl, now extract topic, acls and maybe options too.
                    item["topic"] = data[0]
                    item["acl"] = data[1]

                    # Extract options
                    item["options"] = {}
                    if len(data) == 3:
                        opts = data[2].split(",")
                        for opt in opts:
                            key, value = opt.split("=")
                            item["options"][key] = value
                res.append(item)
            return res
        return(value)
