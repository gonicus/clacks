# -*- coding: utf-8 -*-
import time
import datetime
from clacks.agent.objects.filter import ElementFilter
from clacks.agent.objects.backend.registry import ObjectBackendRegistry


class GetNextID(ElementFilter):
    """
    An object filter which inserts the next free ID for the property
    given as parameter. But only if the current value is empty.

    =============== =======================
    Name            Description
    =============== =======================
    attributeName   The target attribute we want to generate an ID for. uidNumber/gidNumber
    maxValue        The maximum value that would be dsitributed.
    =============== =======================
    """
    def __init__(self, obj):
        super(GetNextID, self).__init__(obj)

    def process(self, obj, key, valDict, attributeName="uidNumber", maxValue=65500):
        if len(valDict[key]['value']) and (valDict[key]['value'][0] == -1):
            maxValue = int(maxValue)

            if len(valDict[key]['backend']) > 1:
                raise Exception("GetNextID filter does not support multiple backends!")

            be = ObjectBackendRegistry.getBackend(valDict[key]['backend'][0])
            gid = be.get_next_id(attributeName)
            if gid > maxValue:
                raise Exception("GID number generation exceeded limitation of %s!" % (maxValue,))
            valDict[key]['value'] = [gid]

        return key, valDict


class ShadowDaysToDate(ElementFilter):
    """
    Converts an integer of days (since 01.01.1970) into a datetime.date object...

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>shadowDaysToDate</Name>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """

    def __init__(self, obj):
        super(ShadowDaysToDate, self).__init__(obj)

    def process(self, obj, key, valDict):
        valDict[key]['value'] = map(lambda x: datetime.date.fromtimestamp(x * 60 * 60 * 24), valDict[key]['value'])
        return key, valDict


class DateToShadowDays(ElementFilter):
    """
    Converts a date object into an a shadow date value. Number of days since 01.01.1970

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>DateToShadowDays</Name>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """

    def __init__(self, obj):
        super(DateToShadowDays, self).__init__(obj)

    def process(self, obj, key, valDict):
        valDict[key]['value'] = map(lambda x: int(time.mktime(x.timetuple()) / (60*60*24)), valDict[key]['value'])
        return key, valDict
