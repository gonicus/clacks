# -*- coding: utf-8 -*-
import gettext
from pkg_resources import resource_filename #@UnresolvedImport
from clacks.agent.objects.comparator import ElementComparator
from clacks.common.components import PluginRegistry
import re

# Include locales
t = gettext.translation('messages', resource_filename("clacks.agent", "locale"), fallback=True)
_ = t.ugettext


class IsValidHostName(ElementComparator):
    """
    Validates a given domain name.
    """

    def __init__(self, obj):
        super(IsValidHostName, self).__init__()

    def process(self, key, value):

        errors = []

        for hostname in value:
            if not re.match("^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$", hostname):
                errors.append(_("The given hostname '%s' is not valid!") % hostname)

        return len(errors) == 0, errors


class IsExistingDN(ElementComparator):
    """
    Validates a given domain name.
    """

    def __init__(self, obj):
        super(IsExistingDN, self).__init__()

    def process(self, key, value):

        errors = []
        index = PluginRegistry.getInstance("ObjectIndex")
        for dn in value:
            if not index.raw_search({'dn': dn}, {'dn': 1}).count():
                errors.append(_("The given dn does not exists '%s'!") % dn)

        return len(errors) == 0, errors


class IsExistingDnOfType(ElementComparator):
    """
    Validates a given domain name.
    """

    def __init__(self, obj):
        super(IsExistingDnOfType, self).__init__()

    def process(self, key, value, objectType):

        errors = []
        index = PluginRegistry.getInstance("ObjectIndex")
        for dn in value:
            if not index.raw_search({'_type': objectType, 'dn': dn}, {'dn': 1}).count():
                errors.append(_("The given dn does not exists '%s'!") % dn)

        return len(errors) == 0, errors


class ObjectWithPropertyExists(ElementComparator):
    """
    Validates a given domain name.
    """

    def __init__(self, obj):
        super(ObjectWithPropertyExists, self).__init__()

    def process(self, key, value, objectType, attribute):

        errors = []
        index = PluginRegistry.getInstance("ObjectIndex")
        for val in value:
            if not index.raw_search({'_type': objectType, attribute: val}, {'dn': 1}).count():
                errors.append(_("There is no '%s' with '%s=%s'!") % (objectType, attribute, val))

        return len(errors) == 0, errors
