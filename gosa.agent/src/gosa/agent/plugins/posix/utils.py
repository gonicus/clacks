# -*- coding: utf-8 -*-
from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.utils import N_
from gosa.common import Environment
from gosa.agent.objects.filter import ElementFilter
from gosa.agent.objects.types import AttributeType
from gosa.agent.objects.backend.registry import ObjectBackendRegistry

import time
import datetime

class GetNextID(ElementFilter):
    """
    An object filter which inserts the next free ID for the property given as parameter.
    But only if the current value is empty.
    """
    def __init__(self, obj):
        super(GetNextID, self).__init__(obj)

    def process(self, obj, key, valDict, attributeName="uidNumber"):
        if len(valDict[key]['value']) and (valDict[key]['value'][0] == -1):
            be = ObjectBackendRegistry.getBackend(valDict[key]['backend'])
            valDict[key]['value'] = [be.get_next_id(attributeName)]

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
        #valDict[key]['backend_type'] = 'Timestamp'
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
        #valDict[key]['backend_type'] = 'Integer'
        return key, valDict
