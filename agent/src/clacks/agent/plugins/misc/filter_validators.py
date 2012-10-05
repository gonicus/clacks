# -*- coding: utf-8 -*-
from clacks.common.components import PluginRegistry
from clacks.common.utils import N_
from clacks.agent.objects.comparator import ElementComparator
import re


class IsValidHostName(ElementComparator):
    """
    Validates a given domain name.
    """

    def __init__(self, obj):
        super(IsValidHostName, self).__init__()

    def process(self, all_props, key, value):

        errors = []

        for hostname in value:
            if not re.match("^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$", hostname):
                errors.append(dict(index=value.index(hostname),
                    detail=N_("invalid hostname '%(hostname)s'"),
                    hostname=hostname))

        return len(errors) == 0, errors


class IsExistingDN(ElementComparator):
    """
    Validates a given domain name.
    """

    def __init__(self, obj):
        super(IsExistingDN, self).__init__()

    def process(self, all_props, key, value):

        errors = []
        index = PluginRegistry.getInstance("ObjectIndex")
        for dn in value:
            if not index.search({'dn': dn}, {'dn': 1}).count():
                errors.append(dict(index=value.index(dn),
                    detail=N_("DN '%(dn)s' does not exist"),
                    dn=dn))


        return len(errors) == 0, errors


class IsExistingDnOfType(ElementComparator):
    """
    Validates a given domain name.
    """

    def __init__(self, obj):
        super(IsExistingDnOfType, self).__init__()

    def process(self, all_props, key, value, objectType):

        errors = []
        index = PluginRegistry.getInstance("ObjectIndex")
        for dn in value:
            if not index.search({'_type': objectType, 'dn': dn}, {'dn': 1}).count():
                errors.append(dict(index=value.index(dn),
                    detail=N_("DN '%(dn)s' does not exist"),
                    dn=dn))

        return len(errors) == 0, errors


class ObjectWithPropertyExists(ElementComparator):
    """
    Validates a given domain name.
    """

    def __init__(self, obj):
        super(ObjectWithPropertyExists, self).__init__()

    def process(self, all_props, key, value, objectType, attribute):

        errors = []
        index = PluginRegistry.getInstance("ObjectIndex")
        for val in value:
            query = {'$or': [{'_type': objectType}, {'_extensions': {'$in': [objectType]}}], attribute: val}
            if not index.search(query, {'dn': 1}).count():
                errors.append(dict(index=value.index(val),
                    detail=N_("no '%(type)s' object with '%(attribute)s' property matching '%(value)s' found"),
                    type=objectType,
                    attribute=attribute,
                    value=val))

        return len(errors) == 0, errors
