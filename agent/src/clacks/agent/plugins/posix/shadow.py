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

import time
import datetime
from clacks.agent.objects.filter import ElementFilter


class ShadowDaysToDatetime(ElementFilter):
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
        super(ShadowDaysToDatetime, self).__init__(obj)

    def process(self, obj, key, valDict):
        valDict[key]['value'] = map(lambda x: datetime.datetime.fromtimestamp(x * 60 * 60 * 24), valDict[key]['value'])
        valDict[key]['backend_type'] = 'Integer'
        return key, valDict


class DatetimeToShadowDays(ElementFilter):
    """
    Converts a date object into an a shadow date value. Number of days since 01.01.1970

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>DatetimeToShadowDays</Name>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """

    def __init__(self, obj):
        super(DatetimeToShadowDays, self).__init__(obj)

    def process(self, obj, key, valDict):
        valDict[key]['value'] = map(lambda x: int(time.mktime(x.timetuple()) / (60 * 60 * 24)) + 1, valDict[key]['value'])
        return key, valDict
