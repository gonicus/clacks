# -*- coding: utf-8 -*-
import gettext
from pkg_resources import resource_filename
from clacks.common.components import PluginRegistry
from clacks.agent.objects.comparator import ElementComparator

# Include locales
t = gettext.translation('messages', resource_filename("clacks.agent", "locale"), fallback=True)
_ = t.ugettext


class IsValidSambaDomainName(ElementComparator):
    """
    Validates a given sambaDomainName.
    """

    def __init__(self, obj):
        super(IsValidSambaDomainName, self).__init__()

    def process(self, key, value, errors=None):
        index = PluginRegistry.getInstance("ObjectIndex")
        domains = index.xquery("collection('objects')/o:SambaDomain//o:sambaDomainName/string()")

        if value[0] in domains:
            return True

        if not errors:
            errors = []

        errors.append(_("The given sambaDomainName '%s' does not exists!") % value[0])

        return False
