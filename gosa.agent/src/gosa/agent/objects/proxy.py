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
    __method_map = {}

    def __init__(self, dn_or_base, what=None):
        self.__env = Environment.getInstance()
        self.__log = getLogger(__name__)
        self.__factory = GOsaObjectFactory.getInstance()

        # Load available object types
        object_types = self.__factory.getObjectTypes()

        base_mode = "update"
        base, extensions = self.__factory.identifyObject(dn_or_base)
        if base == None:
            if what == None:
                raise Exception("the object does not exist - in order to create it, I need to know the target base type")
            if not what in object_types:
                raise Exception("unknown object type '%s'" % what)

            base = what
            base_mode = "create"
            extensions = []

        # Get available extensions
        self.__log.info("loading %s base object for %s" % (base, dn_or_base))
        all_extensions = object_types[base]['extended_by']

        # Load base object and extenions
        self.__base = self.__factory.getObject(base, dn_or_base, mode=base_mode)
        for extension in extensions:
            self.__log.info("loading %s extension for %s" % (extension, dn_or_base))
            self.__extensions[extension] = self.__factory.getObject(extension, self.__base.uuid)
        for extension in all_extensions:
            if extension not in self.__extensions:
                self.__extensions[extension] = None

        # Generate method mapping
        for obj in [base] + extensions:
            for method in object_types[obj]['methods']:
                if obj == self.__base.__class__.__name__:
                    self.__method_map[method] = getattr(self.__base, method)
                    continue
                if obj in self.__extensions:
                    self.__method_map[method] = getattr(self.__extensions[obj], method)

        # Generate read and write mapping for attributes
        self.__attribute_map = self.__factory.getAttributes()

    def extend(self, extension):
        if not extension in self.__extensions:
            raise Exception("extension '%s' not allowed" % extension)

        if self.__extensions[extensions] != None:
            raise Exception("extension '%s' already defined" % extension)

        # Create extension
        self.__extensions[extension] = self.__factory.getObject(extension,
                self.__base.uuid, mode="extend")

    def retract(self, extension):
        if not extension in self.__extensions:
            raise Exception("extension '%s' not allowed" % extension)

        if self.__extensions[extension] == None:
            raise Exception("extension '%s' already retracted" % extension)

        # Immediately remove extension
        #TODO: maybe we want to do that on commit?
        self.__extensions[extension].retract()
        self.__extensions[extension] = None

    def move(self, new_base):
        raise NotImplemented()

    def remove(self, recursive=False):
        raise NotImplemented()

    def commit(self):
        self.__base.commit()

        for extension in self.__extensions:
            extension.commit()

    def __getattr__(self, name):
        # Valid method?
        if name in self.__method_map:
            return self.__method_map[name]

        # Valid attribute?
        if not name in self.__attribute_map:
            raise AttributeError("no such primary attribute '%s'" % name)

        # Load from primary object
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
                continue

        if not found:
            raise AttributeError("no such attribute '%s'" % name)
