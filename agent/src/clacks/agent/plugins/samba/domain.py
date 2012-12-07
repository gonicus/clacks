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

from clacks.common.utils import N_
from zope.interface import implements
from clacks.common.components import Plugin
from clacks.common.handler import IInterfaceHandler
from clacks.common.components import PluginRegistry
from clacks.common.components import Command
from clacks.agent.objects.comparator import ElementComparator


class SambaGuiMethods(Plugin):
    implements(IInterfaceHandler)
    _target_ = 'gosa'
    _priority_ = 80

    @Command(__help__=N_("Returns the current samba domain policy for a given user"))
    def getSambaDomainInformation(self):
        return "Ja"


class IsValidSambaDomainName(ElementComparator):
    """
    Validates a given sambaDomainName.
    """

    def __init__(self, obj):
        super(IsValidSambaDomainName, self).__init__()

    def process(self, all_props, key, value):
        domain = value[0]
        errors = []
        index = PluginRegistry.getInstance("ObjectIndex")

        res = index.search({'_type': 'SambaDomain', 'sambaDomainName': domain},
            {'_uuid': 1})

        if res.count():
            return True, errors

        errors.append(dict(index=0, detail=N_("Unknown domain '%(domain)s'"), domain=value[0]))

        return False, errors
