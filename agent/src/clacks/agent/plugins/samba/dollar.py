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
from clacks.agent.objects.filter import ElementFilter
from clacks.common.error import ClacksErrorHandler as C


class SambaDollarFilterOut(ElementFilter):
    """
    An object filter which can add a '$' after the machines system-ID
    """
    def __init__(self, obj):
        super(SambaDollarFilterOut, self).__init__(obj)

    def process(self, obj, key, valDict):
        if len(valDict[key]['value']) and type(valDict[key]['value'][0]) in [str, unicode]:
            valDict[key]['value'][0] = valDict[key]['value'][0].rstrip("$") + "$"
        else:
            raise ValueError(C.make_error("TYPE_UNKNOWN", self.__class__.__name__, type=type(valDict[key]['value'])))

        return key, valDict


class SambaDollarFilterIn(ElementFilter):
    """
    An object filter which can add a '$' after the machines system-ID
    """
    def __init__(self, obj):
        super(SambaDollarFilterIn, self).__init__(obj)

    def process(self, obj, key, valDict):
        if len(valDict[key]['value']) and type(valDict[key]['value'][0]) in [str, unicode]:
            valDict[key]['value'][0] = valDict[key]['value'][0].rstrip("$")
        else:
            raise ValueError(C.make_error("TYPE_UNKNOWN", self.__class__.__name__, type=type(valDict[key]['value'])))

        return key, valDict
