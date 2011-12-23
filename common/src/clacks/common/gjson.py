# -*- coding: utf-8 -*-
import json
import datetime
import pkg_resources

def dumps(obj, encoding='utf-8'):
    return json.dumps(obj, encoding=encoding, cls=PObjectEncoder)


def loads(json_string, encoding='utf-8'):
    return json.loads(json_string, encoding=encoding, object_hook=PObjectDecoder)


class ServiceException(Exception):
    pass


class ServiceRequestNotTranslatable(ServiceException):
    pass


class BadServiceRequest(ServiceException):
    pass


class JSONDataHandler(object):

    @staticmethod
    def encode(data):
        raise NotImplemented("JSONDataHandler implementation fails to encode")

    @staticmethod
    def decode(data):
        raise NotImplemented("JSONDataHandler implementation fails to decode")

    @staticmethod
    def isinstance(data):
        raise NotImplemented("JSONDataHandler implementation fails to detect")

    @staticmethod
    def canhandle():
        raise NotImplemented("JSONDataHandler implementation fails to commit")


class DateTimeHandler(JSONDataHandler):

    @staticmethod
    def encode(data):
        return  {'object': str(data), '__jsonclass__': 'datetime.datetime'}

    @staticmethod
    def decode(data):
        return datetime.datetime.strptime(dct['object'], "%Y-%m-%d %H:%M:%S")

    @staticmethod
    def isinstance(data):
        return isinstance(data, datetime.datetime)

    @staticmethod
    def canhandle():
        return "datetime.datetime"


class PObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        global json_handlers

        if isinstance(obj, datetime.datetime):
            return {'object': str(obj), '__jsonclass__': 'datetime.datetime'}
        return json.JSONEncoder.default(self, obj)


def PObjectDecoder(dct):
    if '__jsonclass__' in dct:
        clazz = dct['__jsonclass__']
        if clazz == "datetime.datetime":
            return datetime.datetime.strptime(dct['object'], "%Y-%m-%d %H:%M:%S")

        raise NotImplemented("type '%s' is not serializeable" % clazz)
    return dct


# Load our entrypoints
json_handlers = {}
for entry in pkg_resources.iter_entry_points("json.datahandler"):
    mod = entry.load()
    json_handlers[mod.canhandle()] = mod
