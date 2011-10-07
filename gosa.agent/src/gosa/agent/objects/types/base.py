# -*- coding: utf-8 -*-
from gosa.agent.objects.types import AttributeType


class StringAttribute(AttributeType):
    __alias__ = "String"

    @classmethod
    def _convert_to_string(cls, value):
        return(value)

    @classmethod
    def _convert_from_string(cls, value):
        return(value)


class IntegerAttribute(AttributeType):
    __alias__ = "Integer"

    @classmethod
    def _convert_to_integer(cls, value):
        return(value)

    @classmethod
    def _convert_from_integer(cls, value):
        return(value)


class BooleanAttribute(AttributeType):
    __alias__ = "Boolean"

    @classmethod
    def _convert_to_boolean(cls, value):
        return(value)

    @classmethod
    def _convert_from_boolean(cls, value):
        return(value)


class BinaryAttribute(AttributeType):
    __alias__ = "Binary"

    @classmethod
    def _convert_to_binary(cls, value):
        return(value)

    @classmethod
    def _convert_from_binary(cls, value):
        return(value)


class UnicodeStringAttribute(AttributeType):
    __alias__ = "UnicodeString"

    @classmethod
    def _convert_to_unicodestring(cls, value):
        return(value)

    @classmethod
    def _convert_from_unicodestring(cls, value):
        return(value)


class DateAttribute(AttributeType):
    __alias__ = "Date"

    @classmethod
    def _convert_to_date(cls, value):
        return(value)

    @classmethod
    def _convert_from_date(cls, value):
        return(value)


class TimestampAttribute(AttributeType):
    __alias__ = "Timestamp"

    @classmethod
    def _convert_to_timestamp(cls, value):
        return(value)

    @classmethod
    def _convert_from_timestamp(cls, value):
        return(value)
