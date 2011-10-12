# -*- coding: utf-8 -*-
from gosa.agent.objects.types import AttributeType
import datetime

class StringAttribute(AttributeType):
    __alias__ = "String"

    def _convert_to_string(cls, value):
        return(value)

    def _convert_from_string(cls, value):
        return(value)

    def is_valid_value(cls, value):
        return(not len(value) or all(map(lambda x: type(x) == str, value)))

    def values_match(cls, value1, value2):
        return(value1 == value2)


class IntegerAttribute(AttributeType):
    __alias__ = "Integer"

    def _convert_to_integer(cls, value):
        return(value)

    def _convert_from_integer(cls, value):
        return(value)

    def is_valid_value(cls, value):
        return(not len(value) or all(map(lambda x: type(x) == int, value)))

    def values_match(cls, value1, value2):
        return(value1 == value2)


class BooleanAttribute(AttributeType):
    __alias__ = "Boolean"

    def is_valid_value(cls, value):
        return(not len(value) or all(map(lambda x: type(x) == bool, value)))

    def _convert_to_boolean(cls, value):
        return(value)

    def _convert_from_boolean(cls, value):
        return(value)

    def values_match(cls, value1, value2):
        return(value1 == value2)


class BinaryAttribute(AttributeType):
    __alias__ = "Binary"

    def _convert_to_binary(cls, value):
        return(value)

    def _convert_from_binary(cls, value):
        return(value)

    def is_valid_value(cls, value):
        return(not len(value) or all(map(lambda x: type(x) == unicode, value)))

    def values_match(cls, value1, value2):
        return(value1 == value2)


class UnicodeStringAttribute(AttributeType):
    __alias__ = "UnicodeString"

    def _convert_to_unicodestring(cls, value):
        return(value)

    def _convert_from_unicodestring(cls, value):
        return(value)

    def is_valid_value(cls, value):
        return(not len(value) or all(map(lambda x: type(x) == unicode, value)))

    def values_match(cls, value1, value2):
        return(value1 == value2)


class DateAttribute(AttributeType):
    __alias__ = "Date"

    def _convert_to_date(cls, value):
        return(value)

    def _convert_from_date(cls, value):
        return(value)

    def is_valid_value(cls, value):
        return(not len(value) or all(map(lambda x: type(x) == datetime.date, value)))

    def values_match(cls, value1, value2):
        return(value1 == value2)


class TimestampAttribute(AttributeType):
    __alias__ = "Timestamp"

    def _convert_to_timestamp(cls, value):
        return(value)

    def _convert_from_timestamp(cls, value):
        return(value)

    def is_valid_value(cls, value):
        return(not len(value) or all(map(lambda x: type(x) == datetime.datetime, value)))

    def values_match(cls, value1, value2):
        return(value1 == value2)
