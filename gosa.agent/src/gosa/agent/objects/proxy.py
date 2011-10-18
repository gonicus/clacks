# -*- coding: utf-8 -*-
from logging import getLogger
from gosa.common import Environment
from gosa.agent.objects import GOsaObjectFactory


class GOsaObjectProxy(object):
    __env = None
    __log = None
    __base = None
    __extensions = {}
    __factory = None
    __attribute_map = {}

    def __init__(self, dn_or_base, what=None):
        self.__env = Environment.getInstance()
        self.__log = getLogger(__name__)
        self.__factory = GOsaObjectFactory()

        base_mode = "update"
        base, extensions = self.__factory.identifyObject(dn_or_base)
        if base == None:
            if what == None:
                raise Exception("the object does not exist - in order to create it, I need to know the target base type")
            if not what in self.__factory.getObjectTypes():
                raise Exception("unknown object type '%s'" % what)

            base = what
            base_mode = "create"
            extensions = []

        # Get available extensions
        self.__log.info("loading %s base object for %s" % (base, dn_or_base))
        all_extensions = self.__factory.getObjectTypes()[base]['extended_by']

        # Load base object and extenions
        self.__base = self.__factory.getObject(base, dn_or_base, mode=base_mode)
        for extension in extensions:
            self.__log.info("loading %s extension for %s" % (extension, dn_or_base))
            self.__extensions[extension] = self.__factory.getObject(extension, dn_or_base)
        for extension in all_extensions:
            if extension not in self.__extensions:
                self.__extensions[extension] = None

        # Generate read and write mapping for attributes
        self.__attribute_map = self.__factory.getAttributes()

        print "-"*80
        print "Base type:", base
        print "Installed extensions:", extensions
        print "Available extensions:", all_extensions
        print "-"*80

    def extend(self, extension):
        raise NotImplemented()

    def retract(self, extension):
        raise NotImplemented()

    def move(self, new_base):
        raise NotImplemented()

    def remove(self, recursive=False):
        raise NotImplemented()

    def commit(self):
        raise NotImplemented()

    def __getattr__(self, name):
        objs = self.__attribute_map[name]['primary']
        for obj in objs:
            if self.__base.__class__.__name__ == obj:
                return getattr(self.__base, name)

            if obj in self.__extensions:
                return getattr(self.__extensions[obj], name)

        raise AttributeError("no such primary attribute '%s'" % name)

    def __setattr__(self, name, value):
        # Store non property values
        try:
            object.__getattribute__(self, name)
            self.__dict__[name] = value
            return
        except AttributeError:
            pass

        found = False
        for obj in self.__attribute_map[name]['primary'] + self.__attribute_map[name]['objects']:
            if self.__base.__class__.__name__ == obj:
                found = True
                setattr(self.__base, name, value)
                continue

            if obj in self.__extensions:
                found = True
                setattr(self.__extensions[obj], name, value)

        if not found:
            raise AttributeError("no such attribute '%s'" % name)
