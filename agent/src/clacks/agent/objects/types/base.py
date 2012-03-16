# -*- coding: utf-8 -*-
from clacks.agent.objects.types import AttributeType
import datetime


class StringAttribute(AttributeType):
    __alias__ = "String"

    def _convert_from_string(self, value):
        return(value)

    def is_valid_value(self, value):
        return(not len(value) or all(map(lambda x: type(x) == str, value)))

    def values_match(self, value1, value2):
        return(value1 == value2)

    def _convert_to_boolean(self, value):
        return(map(lambda x: not(x in ['', 'false', '0', 'False']), value))

    def _convert_to_string(self, value):
        return(map(lambda x: str(x), value))

    def _convert_to_integer(self, value):
        return(map(lambda x: int(x), value))

    def _convert_to_unicodestring(self, value):
        return(map(lambda x: unicode(x), value))

    def _convert_from_datetime(self, value):
        return(map(lambda x: str(x), value))

    def fixup(self, value):
        return self._convert_to_string(value)


class IntegerAttribute(AttributeType):
    __alias__ = "Integer"

    def _convert_to_integer(self, value):
        return(value)

    def _convert_from_integer(self, value):
        return(value)

    def is_valid_value(self, value):
        return(not len(value) or all(map(lambda x: type(x) == int, value)))

    def values_match(self, value1, value2):
        return(value1 == value2)

    def _convert_to_string(self, value):
        return(map(lambda x: str(x), value))

    def _convert_to_unicodestring(self, value):
        return(map(lambda x: unicode(x), value))

    def _convert_from_string(self, value):
        return(map(lambda x: int(x), value))


class BooleanAttribute(AttributeType):
    __alias__ = "Boolean"

    def is_valid_value(self, value):
        return(not len(value) or all(map(lambda x: type(x) == bool, value)))

    def _convert_to_boolean(self, value):
        return(value)

    def _convert_from_boolean(self, value):
        return(value)

    def values_match(self, value1, value2):
        return(value1 == value2)

    def _convert_to_string(self, value):
        return(map(lambda x: str(x), value))

    def _convert_to_unicodestring(self, value):
        return(map(lambda x: unicode(x), value))

    def _convert_from_string(self, value):
        return(map(lambda x: not(x in ['', 'false', '0', 'False']), value))


class BinaryAttribute(AttributeType):
    __alias__ = "Binary"

    def _convert_to_binary(self, value):
        return(value)

    def _convert_from_binary(self, value):
        return(value)

    def is_valid_value(self, value):
        return(not len(value) or all(map(lambda x: type(x) == unicode, value)))

    def values_match(self, value1, value2):
        return(value1 == value2)

    def _convert_to_string(self, value):
        return(map(lambda x: str(x), value))

    def _convert_to_unicodestring(self, value):
        return(map(lambda x: unicode(x), value))


class UnicodeStringAttribute(AttributeType):
    __alias__ = "UnicodeString"

    def _convert_to_unicodestring(self, value):
        return(value)

    def _convert_from_unicodestring(self, value):
        return(value)

    def is_valid_value(self, value):
        return(not len(value) or all(map(lambda x: type(x) == unicode, value)))

    def values_match(self, value1, value2):
        return(value1 == value2)

    def _convert_to_string(self, value):
        return(map(lambda x: str(x), value))

    def _convert_to_unicodestring(self, value):
        return(map(lambda x: unicode(x), value))

    def _convert_from_string(self, value):
        return(map(lambda x: unicode(x), value))


class DateAttribute(AttributeType):
    __alias__ = "Date"

    def _convert_to_date(self, value):
        return(value)

    def _convert_from_date(self, value):
        return(value)

    def is_valid_value(self, value):
        return(not len(value) or all(map(lambda x: type(x) == datetime.date, value)))

    def values_match(self, value1, value2):
        return(value1 == value2)

    def _convert_to_string(self, value):
        return(map(lambda x: x.strftime("%Y-%m-%d"), value))

    def _convert_to_unicodestring(self, value):
        return(map(lambda x: unicode(x.strftime("%Y-%m-%d")), value))


class TimestampAttribute(AttributeType):
    __alias__ = "Timestamp"

    def _convert_to_timestamp(self, value):
        return(value)

    def _convert_from_timestamp(self, value):
        return(value)

    def is_valid_value(self, value):
        return(not len(value) or all(map(lambda x: type(x) == datetime.datetime, value)))

    def values_match(self, value1, value2):
        return(value1 == value2)

    def _convert_to_string(self, value):
        return(map(lambda x: x.strftime("%Y-%m-%dT%H:%M:%S%z"), value))

    def _convert_to_unicodestring(self, value):
        return(map(lambda x: unicode(x.strftime("%Y-%m-%dT%H:%M:%S%z")), value))
