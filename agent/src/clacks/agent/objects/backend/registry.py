# -*- coding: utf-8 -*-
import pkg_resources
import logging


class ObjectBackendRegistry(object):
    instance = None
    backends = {}
    uuidAttr = "entryUUID"

    def __init__(self):
        log = logging.getLogger("object.backend")
        # Load available backends
        for entry in pkg_resources.iter_entry_points("object.backend"):
            clazz = entry.load()
            ObjectBackendRegistry.backends[clazz.__name__] = clazz()

    def dn2uuid(self, backend, dn):
        return ObjectBackendRegistry.backends[backend].dn2uuid(dn)

    def uuid2dn(self, backend, uuid):
        return ObjectBackendRegistry.backends[backend].uuid2dn(uuid)

    def get_timestamps(self, backend, dn):
        return ObjectBackendRegistry.backends[backend].get_timestamps(dn)

    @staticmethod
    def getInstance():
        if not ObjectBackendRegistry.instance:
            ObjectBackendRegistry.instance = ObjectBackendRegistry()

        return ObjectBackendRegistry.instance

    @staticmethod
    def getBackend(name):
        if not name in ObjectBackendRegistry.backends:
            raise ValueError("no such backend '%s'" % name)

        return ObjectBackendRegistry.backends[name]

    def get_update_dn(self, uuid, data):
        raise NotImplementedError("no way to find new DN implemented")

    def load(self, uuid, info):
        raise NotImplementedError("no way to find new DN implemented")

    def identify(self, dn, params, fixed_rdn=None):
        raise NotImplementedError("no way to find new DN implemented")

    def exists(self, misc):
        raise NotImplementedError("no way to find new DN implemented")

    def remove(self, uuid, recursive=False):
        raise NotImplementedError("no way to find new DN implemented")

    def retract(self, uuid, data, params):
        raise NotImplementedError("no way to find new DN implemented")

    def extend(self, uuid, data, params, foreign_keys):
        raise NotImplementedError("no way to find new DN implemented")

    def move_extension(self, uuid, new_base):
        raise NotImplementedError("no way to find new DN implemented")

    def move(self, uuid, new_base):
        raise NotImplementedError("no way to find new DN implemented")

    def create(self, base, data, params, foreign_keys=None):
        raise NotImplementedError("no way to find new DN implemented")

    def update(self, uuid, data):
        raise NotImplementedError("no way to find new DN implemented")

    def is_uniq(self, attr, value, at_type):
        raise NotImplementedError("no way to find new DN implemented")

    def query(self, base, scope, params, fixed_rdn=None):
        raise NotImplementedError("no way to find new DN implemented")
