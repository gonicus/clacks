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

import smbpasswd #@UnresolvedImport
from clacks.agent.objects.filter import ElementFilter
from clacks.common.error import ClacksErrorHandler as C
from clacks.common.utils import N_


# Register the errors handled  by us
C.register_codes(dict(
    TYPE_UNKNOWN=N_("Filter '%(target)s' does not support input type '%(type)s'")))


class SambaHash(ElementFilter):
    """
    An object filter which generates samba NT/LM Password hashes for the incoming value.
    """
    def __init__(self, obj):
        super(SambaHash, self).__init__(obj)

    def process(self, obj, key, valDict):
        if len(valDict[key]['value']) and type(valDict[key]['value'][0]) in [str, unicode]:
            lm, nt = smbpasswd.hash(valDict[key]['value'][0])
            valDict['sambaNTPassword']['value'] = [nt]
            valDict['sambaLMPassword']['value'] = [lm]
        else:
            raise ValueError(C.make_error("TYPE_UNKNOWN", self.__class__.__name__, type=type(valDict[key]['value'])))

        return key, valDict
