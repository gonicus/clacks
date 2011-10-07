# -*- coding: utf-8 -*-
import inspect
__import__('pkg_resources').declare_namespace(__name__)

class ConversationNotSupported(Exception):
    pass


class AttributeType(object):

    def _cnv_topic(self):
        fname = inspect.stack()[1][3]
        return fname[9:].replace("_", " ")

    def convert_to(target_type, from_v, to_v):
        cnv = getattr(self, "_convert_to_%s" % target_type.lower())
        return cnv(from_v, to_v)

    def convert_from(source_type, from_v, to_v):
        cnv = getattr(self, "_convert_from_%s" % source_type.lower())
        return cnv(from_v, to_v)

    def _convert_to_boolean(self, from_v, to_v):
        raise ConversationNotSupported("cannot convert %s" % self._cnv_topic())

    def _convert_to_string(self, from_v, to_v):
        raise ConversationNotSupported("cannot convert %s" % self._cnv_topic())

    def _convert_to_unicodestring(self, from_v, to_v):
        raise ConversationNotSupported("cannot convert %s" % self._cnv_topic())

    def _convert_to_integer(self, from_v, to_v):
        raise ConversationNotSupported("cannot convert %s" % self._cnv_topic())

    def _convert_to_timestamp(self, from_v, to_v):
        raise ConversationNotSupported("cannot convert %s" % self._cnv_topic())

    def _convert_to_date(self, from_v, to_v):
        raise ConversationNotSupported("cannot convert %s" % self._cnv_topic())

    def _convert_to_binary(self, from_v, to_v):
        raise ConversationNotSupported("cannot convert %s" % self._cnv_topic())

    def _convert_from_boolean(self, from_v, to_v):
        raise ConversationNotSupported("cannot convert %s" % self._cnv_topic())

    def _convert_from_string(self, from_v, to_v):
        raise ConversationNotSupported("cannot convert %s" % self._cnv_topic())

    def _convert_from_unicodestring(self, from_v, to_v):
        raise ConversationNotSupported("cannot convert %s" % self._cnv_topic())

    def _convert_from_integer(self, from_v, to_v):
        raise ConversationNotSupported("cannot convert %s" % self._cnv_topic())

    def _convert_from_timestamp(self, from_v, to_v):
        raise ConversationNotSupported("cannot convert %s" % self._cnv_topic())

    def _convert_from_date(self, from_v, to_v):
        raise ConversationNotSupported("cannot convert %s" % self._cnv_topic())

    def _convert_from_binary(self, from_v, to_v):
        raise ConversationNotSupported("cannot convert %s" % self._cnv_topic())
