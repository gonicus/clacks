# -*- coding: utf-8 -*-
import inspect
__import__('pkg_resources').declare_namespace(__name__)

class ConversationNotSupported(Exception):
    pass


class AttributeType(object):

    def _cnv_topic(self):
        fname = inspect.stack()[1][3]
        if fname[:12:] == "_convert_to_":
            return (self.__alias__.lower(), fname[12:].replace("_", " "))
        else:
            return (self.__alias__.lower(), fname[14:].replace("_", " "))

    def is_valid_value(self, value):
        raise ConversationNotSupported("Cannot check value type for '%s'!" % (self.__alias__.lower(),))

    def values_match(self, value1, value2):
        raise ConversationNotSupported("Value check not implemented for '%s'!" % (self.__alias__.lower(),))

    def convert_to(self, target_type, value):
        cnv = getattr(self, "_convert_to_%s" % target_type.lower())
        return cnv(value)

    def convert_from(self, source_type, value):
        cnv = getattr(self, "_convert_from_%s" % source_type.lower())
        return cnv(value)

    def _convert_to_boolean(self, value):
        raise ConversationNotSupported("Cannot convert from '%s' to '%s'" % self._cnv_topic())

    def _convert_to_string(self, value):
        raise ConversationNotSupported("Cannot convert from '%s' to '%s'" % self._cnv_topic())

    def _convert_to_unicodestring(self, value):
        raise ConversationNotSupported("Cannot convert from '%s' to '%s'" % self._cnv_topic())

    def _convert_to_integer(self, value):
        raise ConversationNotSupported("Cannot convert from '%s' to '%s'" % self._cnv_topic())

    def _convert_to_timestamp(self, value):
        raise ConversationNotSupported("Cannot convert from '%s' to '%s'" % self._cnv_topic())

    def _convert_to_date(self, value):
        raise ConversationNotSupported("Cannot convert from '%s' to '%s'" % self._cnv_topic())

    def _convert_to_binary(self, value):
        raise ConversationNotSupported("Cannot convert from '%s' to '%s'" % self._cnv_topic())

    def _convert_from_boolean(self, value):
        raise ConversationNotSupported("Cannot convert to '%s' from '%s'" % self._cnv_topic())

    def _convert_from_string(self, value):
        raise ConversationNotSupported("Cannot convert to '%s' from '%s'" % self._cnv_topic())

    def _convert_from_unicodestring(self, value):
        raise ConversationNotSupported("Cannot convert to '%s' from '%s'" % self._cnv_topic())

    def _convert_from_integer(self, value):
        raise ConversationNotSupported("Cannot convert to '%s' from '%s'" % self._cnv_topic())

    def _convert_from_timestamp(self, value):
        raise ConversationNotSupported("Cannot convert to '%s' from '%s'" % self._cnv_topic())

    def _convert_from_date(self, value):
        raise ConversationNotSupported("Cannot convert to '%s' from '%s'" % self._cnv_topic())

    def _convert_from_binary(self, value):
        raise ConversationNotSupported("Cannot convert to '%s' from '%s'" % self._cnv_topic())
