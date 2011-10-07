# -*- coding: utf-8 -*-
from gosa.agent.objects.types import AttributeType


class StringAttribute(AttributeType):
    __alias__ = "String"


class IntegerAttribute(AttributeType):
    __alias__ = "Integer"


class BooleanAttribute(AttributeType):
    __alias__ = "Boolean"
