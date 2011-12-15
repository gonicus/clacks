# -*- coding: utf-8 -*-
"""
GOsa Object Proxy
=================

The GOsa object proxy sits on top of the :ref:`gosa.agent.object.factory:GOsaObjectFactory`
and is the glue between objects that are defined via XML descriptions. The proxy should
be used to load, remove and modify objects.

Here are some examples:

    >>> obj = GOsaObjectProxy(u"ou=people,dc=example,dc=net", "User")
    >>> obj.uid = "user1"
    >>> obj.sn = u"Mustermann"
    >>> obj.givenName = u"Eike"
    >>> obj.commit()

This fragment creates a new user on the given base.

    >>> obj.extend('PosixUser')
    >>> obj.homeDirectory = '/home/' + obj.uid
    >>> obj.gidNumber = 4711
    >>> obj.commit()

This fragment will add the *PosixUser* extension to the object, while

    >>> obj.get_extension_types()

will list the available extension types for that specific object.
----
"""
import StringIO
import pkg_resources
from lxml import etree
from base64 import b64encode
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

            # Forward attribute modification to all extension that provide
            # that given value (even if it is foreign)
            if obj in self.__extensions and self.__extensions[obj]:
                found = True
                setattr(self.__extensions[obj], name, value)
                continue

        if not found:
            raise AttributeError("no such attribute '%s'" % name)

    def asXML(self, only_indexed=False):
        """
        Returns XML representations for the base-object and all its extensions.
        """
        atypes = self.__factory.getAttributeTypes()

        # Get the xml definitions combined for all objects.
        xmldefs = etree.tostring(self.__factory.getXMLDefinitionsCombined())

        # Create a document wich contains all necessary information to create
        # xml reprentation of our own.
        # The class-name, all property values and the object definitions
        classtag = etree.Element("class")
        classtag.text = self.__base.__class__.__name__

        # Create a list of all class information required to build an
        # xml represention of this class
        propertiestag = etree.Element("properties")
        attrs = {}
        attrs['dn'] = [self.__base.dn]
        attrs['entry-uuid'] = [self.__base.uuid]
        attrs['modify-date'] = atypes['Timestamp'].convert_to("UnicodeString", [self.__base.modifyTimestamp])

        # Add base class properties
        props = self.__base.getProperties()
        for propname in props:

            # Use the object-type conversion method to get valid item string-representations.
            # This does not work for boolean values, due to the fact that xml requires
            # lowercase (true/false)
            v = props[propname]['value']
            if props[propname]['type'] == "Boolean":
                attrs[propname] = map(lambda x: 'true' if x == True else 'false', v)
            elif props[propname]['type'] == "Binary":
                attrs[propname] = map(lambda x: b64encode(x), v)
            else:
                attrs[propname] = atypes[props[propname]['type']].convert_to("UnicodeString", v)

        # Create a list of extensions and their properties
        exttag = etree.Element("extensions")
        for name in self.__extensions.keys():
            if self.__extensions[name]:
                ext = etree.Element("extension")
                ext.text = name
                exttag.append(ext)

                # Append extension properties to the list of attributes
                # passed to the xsl
                props = self.__extensions[name].getProperties()
                for propname in props:

                    # Use the object-type conversion method to get valid item string-representations.
                    # This does not work for boolean values, due to the fact that xml requires
                    # lowercase (true/false)
                    v = props[propname]['value']
                    if props[propname]['type'] == "Boolean":
                        attrs[propname] = map(lambda x: 'true' if x == True else 'false', v)

                    # Skip binary ones
                    elif props[propname]['type'] == "Binary":
                        attrs[propname] = map(lambda x: b64encode(x), v)

                    # Make remaining values unicode
                    else:
                        attrs[propname] = atypes[props[propname]['type']].convert_to("UnicodeString", v)

        # Build a xml represention of the collected properties
        for key in attrs:

            # Skip empty ones
            if not len(attrs[key]):
                continue

            # Build up xml-elements
            t = etree.Element("property")
            for value in attrs[key]:
                v = etree.Element("value")
                v.text = value
                n = etree.Element('name')
                n.text = key
                t.append(n)
                t.append(v)

            propertiestag.append(t)

        # Combine all collected class info in a single xml file, this
        # enables us to compute things using xsl
        use_index = "<only_indexed>true</only_indexed>" if only_indexed else "<only_indexed>false</only_indexed>"
        xml = "<merge xmlns=\"http://www.gonicus.de/Objects\">%s<defs>%s</defs>%s%s%s</merge>" % (etree.tostring(classtag), \
                xmldefs, etree.tostring(propertiestag), etree.tostring(exttag), use_index)

        # Transform xml-combination into a useable xml-class representation
        xml_doc = etree.parse(StringIO.StringIO(xml))
        xslt_doc = etree.parse(pkg_resources.resource_filename('gosa.agent', 'data/object_to_xml.xsl'))
        transform = etree.XSLT(xslt_doc)
        res = transform(xml_doc)
        return etree.tostring(res)
