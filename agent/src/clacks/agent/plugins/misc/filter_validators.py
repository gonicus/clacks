# -*- coding: utf-8 -*-
import gettext
from pkg_resources import resource_filename
from clacks.agent.objects.comparator import ElementComparator
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

    def process(self, key, value, errors=[]):
        for hostname in value:
            if not re.match("^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$", hostname):
                errors.append(_("The given hostname '%s' is not valid!") % hostname)

        return len(errors) == 0

