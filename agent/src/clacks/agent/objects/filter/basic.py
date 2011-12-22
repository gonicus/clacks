# -*- coding: utf-8 -*-
from clacks.agent.objects.filter import ElementFilter, ElementFilterException
from clacks.agent.objects import GOsaObjectFactory
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
    Add another backend to the existing ones.
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
       </Filter>
      </FilterEntry>
    """
    def __init__(self, obj):
        super(SetValue, self).__init__(obj)

    def process(self, obj, key, valDict, value):
        f = GOsaObjectFactory()
        types = f.getAttributeTypes()
        valDict[key]['value'] = types['String'].convert_to(valDict[key]['type'], [value])
        return key, valDict


class Clear(ElementFilter):
    """
    This filter clears the value of an attribute.
    """
    def __init__(self, obj):
        super(Clear, self).__init__(obj)

    def process(self, obj, key, valDict):
        f = GOsaObjectFactory()
        types = f.getAttributeTypes()
        valDict[key]['value'] = types['String'].convert_to(valDict[key]['type'], [''])
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
