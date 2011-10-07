# -*- coding: utf-8 -*-
from gosa.agent.objects.types import AttributeType
import datetime

class StringAttribute(AttributeType):
    __alias__ = "String"

    @classmethod
    def _convert_to_string(cls, value):
        return(value)

    @classmethod
    def _convert_from_string(cls, value):
        return(value)

    @classmethod
    def is_valid_value(cls, value):
        return(not len(value) or all(map(lambda x: type(x) == str, value)))

    @classmethod
    def values_match(cls, value1, value2):
        return(value1 == value2)


class IntegerAttribute(AttributeType):
    __alias__ = "Integer"

    @classmethod
    def _convert_to_integer(cls, value):
        return(value)

    @classmethod
    def _convert_from_integer(cls, value):
        return(value)

    @classmethod
    def is_valid_value(cls, value):
        return(not len(value) or all(map(lambda x: type(x) == int, value)))

    @classmethod
    def values_match(cls, value1, value2):
        return(value1 == value2)


class BooleanAttribute(AttributeType):
    __alias__ = "Boolean"

    @classmethod
    def is_valid_value(cls, value):
        return(not len(value) or all(map(lambda x: type(x) == bool, value)))

    @classmethod
    def _convert_to_boolean(cls, value):
        return(value)

    @classmethod
    def _convert_from_boolean(cls, value):
        return(value)

    @classmethod
    def values_match(cls, value1, value2):
        return(value1 == value2)


class BinaryAttribute(AttributeType):
    __alias__ = "Binary"

    @classmethod
    def _convert_to_binary(cls, value):
        return(value)

    @classmethod
    def _convert_from_binary(cls, value):
        return(value)

    @classmethod
    def is_valid_value(cls, value):
        return(not len(value) or all(map(lambda x: type(x) == unicode, value)))

    @classmethod
    def values_match(cls, value1, value2):
        return(value1 == value2)


class UnicodeStringAttribute(AttributeType):
    __alias__ = "UnicodeString"

    @classmethod
    def _convert_to_unicodestring(cls, value):
        return(value)

    @classmethod
    def _convert_from_unicodestring(cls, value):
        return(value)

    @classmethod
    def is_valid_value(cls, value):
        return(not len(value) or all(map(lambda x: type(x) == unicode, value)))

    @classmethod
    def values_match(cls, value1, value2):
        return(value1 == value2)


class DateAttribute(AttributeType):
    __alias__ = "Date"

    @classmethod
    def _convert_to_date(cls, value):
        return(value)

    @classmethod
    def _convert_from_date(cls, value):
        return(value)

    @classmethod
    def is_valid_value(cls, value):
        return(not len(value) or all(map(lambda x: type(x) == datetime.date, value)))

    @classmethod
    def values_match(cls, value1, value2):
        return(value1 == value2)


class TimestampAttribute(AttributeType):
    __alias__ = "Timestamp"

    @classmethod
    def _convert_to_timestamp(cls, value):
        return(value)

    @classmethod
    def _convert_from_timestamp(cls, value):
        return(value)

    @classmethod
    def is_valid_value(cls, value):
        return(not len(value) or all(map(lambda x: type(x) == datetime.datetime, value)))

    @classmethod
    def values_match(cls, value1, value2):
        return(value1 == value2)
