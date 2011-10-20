# -*- coding: utf-8 -*-
from ldap.dn import str2dn, dn2str
from logging import getLogger
from gosa.common import Environment
from gosa.agent.objects import GOsaObjectFactory


class ProxyException(Exception):
    pass


class GOsaObjectProxy(object):
    dn = None
    uuid = None
    __env = None
    __log = None
    __base = None
    __extensions = None
    __factory = None
    __attribute_map = None
    __method_map = None

    def __init__(self, dn_or_base, what=None):
        self.__env = Environment.getInstance()
        self.__log = getLogger(__name__)
        self.__factory = GOsaObjectFactory.getInstance()
        self.__base = None
        self.__extensions = {}
        self.__attribute_map = {}
        self.__method_map = {}

        # Load available object types
        object_types = self.__factory.getObjectTypes()

        base_mode = "update"
        base, extensions = self.__factory.identifyObject(dn_or_base)
        if what:
            if not what in object_types:
                raise ProxyException("unknown object type '%s'" % what)

            base = what
            base_mode = "create"
            extensions = []

        if not base:
            raise ProxyException("object '%s' not found" % dn_or_base)

        # Get available extensions
        self.__log.debug("loading %s base object for %s" % (base, dn_or_base))
        all_extensions = object_types[base]['extended_by']

        # Load base object and extenions
        self.__base = self.__factory.getObject(base, dn_or_base, mode=base_mode)
        for extension in extensions:
            self.__log.debug("loading %s extension for %s" % (extension, dn_or_base))
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

        self.uuid = self.__base.uuid
        self.dn = self.__base.dn

    def get_parent_dn(self):
        return dn2str(str2dn(self.__base.dn.encode('utf-8'))[1:]).decode('utf-8')

    def get_base_type(self):
        return self.__base.__class__.__name__

    def get_extension_types(self):
        return dict([(e, i != None) for e, i in self.__extensions.iteritems()])

    def extend(self, extension):
        if not extension in self.__extensions:
            raise ProxyException("extension '%s' not allowed" % extension)

        if self.__extensions[extension] != None:
            raise ProxyException("extension '%s' already defined" % extension)

        # Create extension
        self.__extensions[extension] = self.__factory.getObject(extension,
                self.__base.uuid, mode="extend")

    def retract(self, extension):
        if not extension in self.__extensions:
            raise ProxyException("extension '%s' not allowed" % extension)

        if self.__extensions[extension] == None:
            raise ProxyException("extension '%s' already retracted" % extension)

        # Immediately remove extension
        self.__extensions[extension].retract()
        self.__extensions[extension] = None

    def move(self, new_base, recursive=False):
        raise NotImplemented()

    def remove(self, recursive=False):
        if recursive:
            raise NotImplemented("recursive remove is not implemented")

        else:
            # Test if we've children
            if len(self.__factory.getObjectChildren(self.__base.dn)):
                raise ProxyException("specified object has children - use the recursive flag to remove them")

        for extension in [e for x, e in self.__extensions.iteritems() if e]:
            extension.remove()

        self.__base.remove()

    def commit(self):
        self.__base.commit()

        for extension in [e for x, e in self.__extensions.iteritems() if e]:
            extension.commit()

    def __repr__(self):
        return "<wopper>"

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
