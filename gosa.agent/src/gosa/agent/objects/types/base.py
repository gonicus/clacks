# -*- coding: utf-8 -*-
from gosa.agent.objects.types import AttributeType


class StringAttribute(AttributeType):
    __alias__ = "String"


class IntegerAttribute(AttributeType):
    __alias__ = "Integer"


class BooleanAttribute(AttributeType):
    __alias__ = "Boolean"


class BinaryAttribute(AttributeType):
    __alias__ = "Binary"


class UnicodeStringAttribute(AttributeType):
    __alias__ = "UnicodeString"


class DateAttribute(AttributeType):
    __alias__ = "Date"


class TimestampAttribute(AttributeType):
    __alias__ = "Timestamp"
