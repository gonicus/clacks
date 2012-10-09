# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

import pkg_resources
from clacks.common.utils import N_
from clacks.agent.error import ClacksErrorHandler as C


# Register the errors handled  by us
C.register_codes(dict(
    BACKEND_NOT_FOUND=N_("Backend '%(topic)s' not found"),
    ))


class ObjectBackendRegistry(object):
    instance = None
    backends = {}
    uuidAttr = "entryUUID"

    def __init__(self):
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
            raise ValueError(C.make_error("BACKEND_NOT_FOUND", name))

        return ObjectBackendRegistry.backends[name]

    def load(self, uuid, info):
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", None, method="load"))

    def identify(self, dn, params, fixed_rdn=None):
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", None, method="identify"))

    def exists(self, misc):
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", None, method="exists"))

    def remove(self, uuid, data, params):
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", None, method="remove"))

    def retract(self, uuid, data, params):
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", None, method="retract"))

    def extend(self, uuid, data, params, foreign_keys):
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", None, method="extend"))

    def move_extension(self, uuid, new_base):
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", None, method="move_extension"))

    def move(self, uuid, new_base):
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", None, method="move"))

    def create(self, base, data, params, foreign_keys=None):
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", None, method="create"))

    def update(self, uuid, data):
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", None, method="update"))

    def is_uniq(self, attr, value, at_type):
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", None, method="is_uniq"))

    def query(self, base, scope, params, fixed_rdn=None):
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", None, method="query"))
