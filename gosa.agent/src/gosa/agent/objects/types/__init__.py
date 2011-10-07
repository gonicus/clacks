# -*- coding: utf-8 -*-
import inspect
__import__('pkg_resources').declare_namespace(__name__)

class ConversationNotSupported(Exception):
    pass


class AttributeType(object):

    @classmethod
    def _cnv_topic(cls):
        fname = inspect.stack()[1][3]
        if fname[12::] == "_convert_to_":
            return (cls.__alias__.lower(), fname[12:].replace("_", " "))
        else:
            return (cls.__alias__.lower(), fname[14:].replace("_", " "))

    @classmethod
    def is_valid_value(cls, value):
        raise ConversationNotSupported("Cannot check value type for '%s'!" % (cls.__alias__.lower(),))

    @classmethod
    def values_match(cls, value1, value2):
        raise ConversationNotSupported("Value check not implemented for '%s'!" % (cls.__alias__.lower(),))

    @classmethod
    def convert_to(cls, target_type, value):
        cnv = getattr(cls, "_convert_to_%s" % target_type.lower())
        return cnv(value)

    @classmethod
    def convert_from(cls, source_type, value):
        cnv = getattr(cls, "_convert_from_%s" % source_type.lower())
        return cnv(value)

    @classmethod
    def _convert_to_boolean(cls, value):
        raise ConversationNotSupported("Cannot convert from '%s' to '%s'" % cls._cnv_topic())

    @classmethod
    def _convert_to_string(cls, value):
        raise ConversationNotSupported("Cannot convert from '%s' to '%s'" % cls._cnv_topic())

    @classmethod
    def _convert_to_unicodestring(cls, value):
        raise ConversationNotSupported("Cannot convert from '%s' to '%s'" % cls._cnv_topic())

    @classmethod
    def _convert_to_integer(cls, value):
        raise ConversationNotSupported("Cannot convert from '%s' to '%s'" % cls._cnv_topic())

    @classmethod
    def _convert_to_timestamp(cls, value):
        raise ConversationNotSupported("Cannot convert from '%s' to '%s'" % cls._cnv_topic())

    @classmethod
    def _convert_to_date(cls, value):
        raise ConversationNotSupported("Cannot convert from '%s' to '%s'" % cls._cnv_topic())

    @classmethod
    def _convert_to_binary(cls, value):
        raise ConversationNotSupported("Cannot convert from '%s' to '%s'" % cls._cnv_topic())

    @classmethod
    def _convert_from_boolean(cls, value):
        raise ConversationNotSupported("Cannot convert to '%s' from '%s'" % cls._cnv_topic())

    @classmethod
    def _convert_from_string(cls, value):
        raise ConversationNotSupported("Cannot convert to '%s' from '%s'" % cls._cnv_topic())

    @classmethod
    def _convert_from_unicodestring(cls, value):
        raise ConversationNotSupported("Cannot convert to '%s' from '%s'" % cls._cnv_topic())

    @classmethod
    def _convert_from_integer(cls, value):
        raise ConversationNotSupported("Cannot convert to '%s' from '%s'" % cls._cnv_topic())

    @classmethod
    def _convert_from_timestamp(cls, value):
        raise ConversationNotSupported("Cannot convert to '%s' from '%s'" % cls._cnv_topic())

    @classmethod
    def _convert_from_date(cls, value):
        raise ConversationNotSupported("Cannot convert to '%s' from '%s'" % cls._cnv_topic())

    @classmethod
    def _convert_from_binary(cls, value):
        raise ConversationNotSupported("Cannot convert to '%s' from '%s'" % cls._cnv_topic())
