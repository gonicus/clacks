# -*- coding: utf-8 -*-
import pkg_resources
import logging
from clacks.common import Environment


class ObjectRegistry(object):
    """
    Object registry class. The registry holds object instances
    that are currently in use by clients. Objects can be either
    registered manually using::

        >>> from clacks.common.components import ObjectRegistry
        >>> ObjectRegistry.register("the.unique.object.oid", ObjectToRegister)

    The preferred way to register objects is to use the setuptools
    section ```[gosa.objects]```::

        [gosa.objects]
        the.unique.object.oid = full.path.to.the:ObjectToRegister

    In this case, all objects are registered after the agent is fired
    up automatically.
    """
    objects = {}
    _instance = None

    def __init__(self):
        for entry in pkg_resources.iter_entry_points('gosa.objects'):
            ObjectRegistry.register(entry.name, entry.load())

    @staticmethod
    def register(oid, obj):
        """
        Register the given object at the provided OID.
        """
        if oid in  ObjectRegistry.objects:
            raise ValueError("OID '%s' is already registerd!" % oid)

        log = logging.getLogger(__name__)
        log.debug("registered object OID '%s'" % oid)
        ObjectRegistry.objects[oid] = {
            'object': obj,
            'signature': None}

    @staticmethod
    def getInstance():
        """
        Act as a singleton and return an instance of ObjectRegistry.
        """
        if not ObjectRegistry._instance:
            ObjectRegistry._instance = ObjectRegistry()

        return ObjectRegistry