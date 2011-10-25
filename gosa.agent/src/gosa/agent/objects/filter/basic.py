# -*- coding: utf-8 -*-
from gosa.agent.objects.filter import ElementFilter, ElementFilterException
import copy
import time
import datetime

class Target(ElementFilter):
    """
    This filter renames the attribute.
    e.g.::

      <FilterEntry>
       <Filter>
        <Name>Target</Name>
        <Param>passwordMethod</Param>
       </Filter>
      </FilterEntry>
    """
    def __init__(self, obj):
        super(Target, self).__init__(obj)

    def process(self, obj, key, valDict, new_key):
        if key != new_key:
            valDict[new_key] = valDict[key]
            del(valDict[key])
        return new_key, valDict


class SetBackends(ElementFilter):
    """
    This filter allows to change the target backend of an attrbiute.
    It also allows to specify a various amount of backends, see example below.
    e.g.::

      <FilterEntry>
       <Filter>
        <Name>SetBackends</Name>
        <Param>LDAP</Param>
        <Param>NULL</Param>
        <Param>...</Param>
       </Filter>
      </FilterEntry>
    """
    def __init__(self, obj):
        super(SetBackends, self).__init__(obj)

    def process(self, obj, key, valDict, *new_backends):
        valDict[key]['backend'] = list(new_backends)
        return key, valDict


class AddBackend(ElementFilter):
    """
    """
    def __init__(self, obj):
        super(AddBackend, self).__init__(obj)

    def process(self, obj, key, valDict, new_backend):
        valDict[key]['backend'].append(new_backend)
        return key, valDict


class SetValue(ElementFilter):
    """
    This filter allows to change the value of an attrbiute.
    e.g.::

      <FilterEntry>
       <Filter>
        <Name>SetValue</Name>
        <Param>Hallo mein name ist Peter</Param>
        <Param>UnicodeString</Param>
       </Filter>
      </FilterEntry>
    """
    def __init__(self, obj):
        super(SetValue, self).__init__(obj)

    def process(self, obj, key, valDict, value, vtype="String"):

        #TODO: Handle all possible property types and remember! Values are lists always.
        if vtype == "String":
            valDict[key]['value'] = str(value)
        else:
            raise ElementFilterException("Invalid type value (%s) given for filter '%s'!" % (vtype,'SetValue'))
        return key, valDict


class Clear(ElementFilter):
    """
    This filter clears the value of an attribute.
    """
    def __init__(self, obj):
        super(Clear, self).__init__(obj)

    def process(self, obj, key, valDict):
        valDict[key]['value'] = ['']
        return key, valDict


class IntegerToDatetime(ElementFilter):
    """
    Converts an integer object into a datetime.datetime object..

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>IntegerToDatetime</Name>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """

    def __init__(self, obj):
        super(IntegerToDatetime, self).__init__(obj)

    def process(self, obj, key, valDict):
        valDict[key]['value'] = map(lambda x: datetime.datetime.fromtimestamp(x), valDict[key]['value'])
        valDict[key]['backend_type'] = 'Timestamp'
        return key, valDict


class DatetimeToInteger(ElementFilter):
    """
    Converts a timestamp object into an integer value ...

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>DatetimeToInteger</Name>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """

    def __init__(self, obj):
        super(DatetimeToInteger, self).__init__(obj)

    def process(self, obj, key, valDict):
        valDict[key]['value'] = map(lambda x: int(time.mktime(x.timetuple())), valDict[key]['value'])
        valDict[key]['backend_type'] = 'Integer'
        return key, valDict
