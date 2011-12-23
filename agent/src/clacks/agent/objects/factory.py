# -*- coding: utf-8 -*-
"""

Object Factory
==============

Short description
^^^^^^^^^^^^^^^^^

The object factory provides access to backend-data in an object
oriented way. You can create, read, update and delete objects easily.

What object-types are avaialable is configured using XML files, these files
are located here: ``./clacks.common/src/clacks/common/data/objects/``.

Each XML file can contain multiple object definitions, with object related
information, like attributes, methods, how to store and read
objects.

(For a detailed documentation of the of XML files, please have a look at the
./doc directory)

A python meta-class will be created for each object-definition.
Those meta-classes will then be used to instantiate a new python object,
which will then provide the defined attributes, methods, aso.

Here are some examples on how to instatiate on new object:

>>> from clacks.agent.objects import ObjectFactory
>>> f = ObjectFactory.getInstance()
>>> person = f.getObject('Person', "410ad9f0-c4c0-11e0-962b-0800200c9a66")
>>> print person->sn
>>> person->sn = "Surname"
>>> person->commit()

"""
import pkg_resources
import os
import re
import logging
import zope.event
import ldap
import ldap.dn
import StringIO
from lxml import etree, objectify
from clacks.common import Environment
from clacks.common.components import PluginRegistry
from clacks.agent.objects.filter import get_filter
from clacks.agent.objects.backend.registry import ObjectBackendRegistry
from clacks.agent.objects.comparator import get_comparator
from clacks.agent.objects.operator import get_operator
from clacks.agent.objects.object import Object, ObjectChanged

# Status
STATUS_OK = 0
STATUS_CHANGED = 1

# Scopes
SCOPE_BASE = ldap.SCOPE_BASE
SCOPE_ONE = ldap.SCOPE_ONELEVEL
SCOPE_SUB = ldap.SCOPE_SUBTREE

_is_uuid = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')


def load(attr, element, default=None):
    """
    Helper function for loading XML attributes with defaults.
    """
    if not element in attr.__dict__:
        return default

    return attr[element]


class FactoryException(Exception):
        pass


class ObjectFactory(object):
    """
    This class reads object defintions and generates python-meta classes
    for each object, which can then be instantiated using
    :meth:`clacks.agent.objects.factory.ObjectFactory.getObject`.
    """
    __instance = None
    __xml_defs = {}
    __classes = {}
    __var_regex = re.compile('^[a-z_][a-z0-9\-_]*$', re.IGNORECASE)
    __attribute_type = {}
    __object_types = {}
    __xml_objects_combined = None

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

        # Initialize backend registry
        ObjectBackendRegistry.getInstance()

        # Loade attribute type mapping
        for entry in pkg_resources.iter_entry_points("object.type"):
            module = entry.load()
            self.log.info("attribute type %s included" % module.__alias__)
            self.__attribute_type[module.__alias__] = module()

        # Initialize parser
        #pylint: disable=E1101
        schema_path = pkg_resources.resource_filename('clacks.agent', 'data/objects/object.xsd')
        schema_doc = open(schema_path).read()

        # Prepare list of object types
        object_types = ""
        for o_type in self.__attribute_type.keys():
            object_types += "<enumeration value=\"%s\"></enumeration>" % (o_type,)

        # Insert available object types into the xsd schema
        schema_doc = schema_doc % {'object_types': object_types}

        schema_root = etree.XML(schema_doc)
        schema = etree.XMLSchema(schema_root)
        self.__parser = objectify.makeparser(schema=schema)

        self.log.info("object factory initialized")

        # Load and parse schema
        self.load_schema()
        self.load_object_types()

    def getAttributeTypes(self):
        return(self.__attribute_type)

    def getXMLDefinitionsCombined(self):
        """
        Returns a complete XML of all defined objects.
        """
        return self.__xml_objects_combined

    def getIndexedAttributes(self):
        """
        Returns a list of attributes that have to be indexed.
        """
        res = []
        for element in self.__xml_defs.values():

            # Get all <Attribute> tags and check if the property NotIndexed exists
            # and isn't set to 'true'
            find = objectify.ObjectPath("Object.Attributes.Attribute")
            if find.hasattr(element):
                for attr in find(element):
                    if bool(load(attr, "NotIndexed", True)):
                        res.append(attr.Name.text)
        return res

    def getReferences(self, s_obj=None, s_attr=None):
        """
        Returns a dictionary containing all attribute references.
        e.g. A groups memberlist may have references to users.
            {'PosixGroup': {'memberUid': [('PosixUser', 'uid')]}}
        """
        res = {}
        for element in self.__xml_defs.values():

            # Get all <Attributes> tag and iterate through their children
            find = objectify.ObjectPath("Object.Attributes")
            if find.hasattr(element):
                for attr in find(element).iterchildren():

                    # Extract the objects name.
                    obj = attr.getparent().getparent().Name.text

                    # Extract reference information
                    if bool(load(attr, "References", False)):

                        # Ensure that values are initialized
                        if obj not in res:
                            res[obj] = {}

                        # Append the result if it matches the given parameters.
                        res[obj][attr.Name.text] = []
                        for ref in attr.References.iterchildren():
                            if (s_obj == None or s_obj == ref.Object.text) or (s_attr == None or s_attr == ref.Attribute.text):
                                res[obj][attr.Name.text].append((ref.Object.text, ref.Attribute.text))

        return res

    def getAttributes(self):
        """
        Returns a list of all object-attributes
        Including information about primary/foreign attributes.
        """
        res = {}
        for element in self.__xml_defs.values():
            find = objectify.ObjectPath("Object.Attributes")
            if find.hasattr(element):
                for attr in find(element).iterchildren():
                    obj = attr.getparent().getparent().Name.text
                    if not attr.Name.text in res:
                        res[attr.Name.text] = {
                            'description': attr.Description.text,
                            'type': attr.Type.text,
                            'multivalue': bool(load(attr, "MultiValue", False)),
                            'mandatory': bool(load(attr, "Mandatory", False)),
                            'read-only': bool(load(attr, "ReadOnly", False)),
                            'case-sensitive': bool(load(attr, "CaseSensitive", False)),
                            'unique': bool(load(attr, "Unique", False)),
                            'objects': [],
                            'primary': [],
                            }
                    if bool(load(attr, "Foreign", False)):
                        res[attr.Name.text]['objects'].append(obj)
                    else:
                        res[attr.Name.text]['primary'].append(obj)
        return res

    def load_object_types(self):
        types = {}
        extends = {}

        # First, find all base objects
        # -> for every base object -> ask the primary backend to identify [true/false]
        for name, obj in self.__xml_defs.items():
            t_obj = obj
            is_base = bool(t_obj.BaseObject)
            backend = str(t_obj.Backend)
            backend_attrs = self.__get_backend_parameters(t_obj)

            methods = []
            if hasattr(t_obj, "Methods"):
                for method in t_obj.Methods.iterchildren():
                    methods.append(method.Name.text)

            types[name] = {
                'backend': backend,
                'backend_attrs': backend_attrs,
                'extended_by': [],
                'methods': methods,
                'base': is_base,
            }

            if "Extends" in t_obj.__dict__:
                types[str(t_obj.Name)]['extends'] = [str(v) for v in t_obj.Extends.Value]
                for ext in types[name]['extends']:
                    if ext not in extends:
                        extends[ext] = []
                    extends[ext].append(name)

            if "Container" in t_obj.__dict__:
                types[str(t_obj.Name)]['container'] = [str(v) for v in t_obj.Container.Type]

        for name, ext in extends.items():
            if not name in types:
                continue
            types[name]['extended_by'] = ext

        self.__object_types = types

    def getObjectTypes(self):
        return self.__object_types

    def identifyObject(self, dn):
        id_base = None
        id_base_fixed = None
        id_extend = []

        # First, find all base objects
        for name, info in self.__object_types.items():
            be = ObjectBackendRegistry.getBackend(info['backend'])
            classr = self.__xml_defs[name]
            fixed_rdn = classr.FixedRDN.text if 'FixedRDN' in classr.__dict__ else None

            if be.identify(dn, info['backend_attrs'], fixed_rdn):

                if info['base']:
                    if fixed_rdn:
                        if id_base_fixed:
                            raise FactoryException("looks like '%s' beeing '%s' and '%s' at the same time - multiple base objects are not supported" % (dn, id_base, name))
                        id_base_fixed = name

                    else:
                        if id_base:
                            raise FactoryException("looks like '%s' beeing '%s' and '%s' at the same time - multiple base objects are not supported" % (dn, id_base, name))
                        id_base = name
                else:
                    id_extend.append(name)

        if id_base or id_base_fixed:
            return (id_base_fixed or id_base, id_extend)

        return None, None

    def getObjectChildren(self, dn):
        res = {}

        # Identify possible children types
        ido = self.identifyObject(dn)
        if ido[0]:
            o_type = ido[0]
            o = self.__xml_defs[o_type]

            if 'Container' in o.__dict__:

                # Ask base backends for a one level query
                for c_type in o.Container.iterchildren():
                    c = self.__xml_defs[c_type.text]

                    be = ObjectBackendRegistry.getBackend(c.Backend.text)
                    fixed_rdn = c.FixedRDN.text if 'FixedRDN' in c.__dict__ else None
                    for r in be.query(dn, scope=SCOPE_ONE,
                            params=self.__get_backend_parameters(c),
                            fixed_rdn=fixed_rdn):
                        res[r] = c_type.text

        else:
            self.log.warning("cannot identify child %s" % dn)

        return res

    def getObject(self, name, *args, **kwargs):
        """
        Returns a object instance.

        e.g.:

        >>> person = f.getObject('Person', "410ad9f0-c4c0-11e0-962b-0800200c9a66")

        """
        self.log.debug("object of type '%s' requested %s" % (name, args))
        if not name in self.__classes:
            self.__classes[name] = self.__build_class(name)

        return self.__classes[name](*args, **kwargs)

    def load_schema(self):
        """
        This method reads all object defintion files (xml) and combines
        into one single xml-dump.

        This combined-xml-dump will then be forwarded to
        :meth:`clacks.agent.objects.factory.ObjectFactory.__parse_schema`
        to generate meta-classes for each object.

        This meta-classes can then be used to instantiate those objects.
        """
        #pylint: disable=E1101
        path = pkg_resources.resource_filename('clacks.agent', 'data/objects')

        # Include built in schema
        schema_paths = []
        for f in [n for n in os.listdir(path) if n.endswith(os.extsep + 'xml')]:
            schema_paths.append(os.path.join(path, f))

        # Include additional schema configuration
        path = os.path.join(self.env.config.getBaseDir(), 'schema')
        if os.path.isdir(path):
            for f in [n for n in os.listdir(path) if n.endswith(os.extsep + 'xml')]:
                schema_paths.append(os.path.join(path, f))

        # Combine all object definition file into one single doc
        xstr = "<Paths xmlns=\"http://www.gonicus.de/Objects\">";
        for path in schema_paths:
            xstr += "<Path>%s</Path>" % path
        xstr += "</Paths>";

        # Now combine all files into one single xml construct
        xml_doc = etree.parse(StringIO.StringIO(xstr))
        xslt_doc = etree.parse(pkg_resources.resource_filename('clacks.agent', 'data/combine_objects.xsl'))
        transform = etree.XSLT(xslt_doc)
        self.__xml_objects_combined = transform(xml_doc)
        self.__parse_schema(etree.tostring(self.__xml_objects_combined))

    def __parse_schema(self, schema):
        """
        Parses a schema definition
        :meth:`clacks.agent.objects.factory.ObjectFactory.__parser`
        method.
        """
        try:
            xml = objectify.fromstring(schema, self.__parser)
            find = objectify.ObjectPath("Objects.Object")
            if find.hasattr(xml):
                for attr in find(xml):
                    self.__xml_defs[str(attr['Name'])] = attr
                    self.log.info("loaded schema for '%s'" % (str(attr['Name'])))

        except etree.XMLSyntaxError as e:
            raise FactoryException("Error loading object-schema file: %s, %s" % (path, e))

    def __build_class(self, name):
        """
        This method builds a meta-class for each object defintion read from the
        xml defintion files.

        It uses a base-meta-class which will be extended by the define
        attributes and mehtods of the object.

        The final meta-class will be stored and can then be requested using:
        :meth:`clacks.agent.objects.factory.ObjectFactory.getObject`
        """

        self.log.debug("building meta-class for object-type '%s'" % (name,))

        class klass(Object):

            #pylint: disable=E0213
            def __init__(me, *args, **kwargs):
                Object.__init__(me, *args, **kwargs)

            #pylint: disable=E0213
            def __setattr__(me, name, value):
                me._setattr_(name, value)

            #pylint: disable=E0213
            def __getattr__(me, name):
                return me._getattr_(name)

            #pylint: disable=E0213
            def __delattr__(me, name):
                me._delattr_(name)


        # Collect Backend attributes per Backend
        back_attrs = {}
        classr = self.__xml_defs[name]
        if "BackendParameters" in classr.__dict__:
            for entry in classr["BackendParameters"]:
                back_attrs[str(entry.Backend)] = entry.Backend.attrib

        # Collect extends lists. A list of objects that we can extend.
        extends = []
        if "Extends" in classr.__dict__:
            for entry in classr["Extends"]:
                extends.append(str(entry.Value))

        # Load object properties like: is base object and allowed container elements
        base_object = bool(classr['BaseObject']) if "BaseObject" in classr.__dict__ else False
        container = []
        if "Container" in classr.__dict__:
            for entry in classr["Container"]:
                container.append(str(entry.Type))

        # Load FixedRDN value
        fixed_rdn = None
        if "FixedRDN" in classr.__dict__:
            fixed_rdn = str(classr.FixedRDN)

        # Tweak name to the new target
        setattr(klass, '__name__', name)
        setattr(klass, '_objectFactory', self)
        setattr(klass, '_backend', str(classr.Backend))
        setattr(klass, '_displayName', str(classr.DisplayName))
        setattr(klass, '_fixedRDN', fixed_rdn)
        setattr(klass, '_backendAttrs', back_attrs)
        setattr(klass, '_extends', extends)
        setattr(klass, '_base_object', base_object)
        setattr(klass, '_container_for', container)

        # Prepare property and method list.
        props = {}
        methods = {}

        # Add documentation if available
        if 'Description' in classr.__dict__:
            setattr(klass, '_description', str(classr['Description']))

        # Load the backend and its attributes
        defaultBackend = str(classr.Backend)

        # Append attributes
        if 'Attributes' in classr.__dict__:
            for prop in classr['Attributes']['Attribute']:

                self.log.debug("adding property: '%s'" % (str(prop['Name']),))

                # Read backend definition per property (if it exists)
                backend = defaultBackend
                if "Backend" in prop.__dict__:
                    backend = str(prop.Backend)

                # Do we have an output filter definition?
                out_f = []
                if "OutFilter" in prop.__dict__:
                    for entry in  prop['OutFilter'].iterchildren():
                        self.log.debug(" appending out-filter")
                        of = self.__handleFilterChain(entry)
                        out_f.append(of)

                # Do we have a input filter definition?
                in_f =  []
                if "InFilter" in prop.__dict__:
                    for entry in  prop['InFilter'].iterchildren():
                        self.log.debug(" appending in-filter")
                        in_f.append(self.__handleFilterChain(entry))

                # Read and build up validators
                validator =  None
                if "Validators" in prop.__dict__:
                    self.log.debug(" appending property validator")
                    validator = self.__build_filter(prop['Validators'])

                # Read the properties syntax
                syntax = str(prop['Type'])
                backend_syntax = syntax
                if "BackendType" in prop.__dict__:
                    backend_syntax = str(prop['BackendType'])

                # Read blocked by settings - When they are fullfilled, these property cannot be changed.
                blocked_by = []
                if "BlockedBy" in prop.__dict__:
                    name = str(prop['BlockedBy'].Name)
                    value = str(prop['BlockedBy'].Value)
                    blocked_by.append({'name': name, 'value': value})

                # Convert the default to the corresponding type.
                default = None
                if "Default" in prop.__dict__:
                    default = self.__attribute_type['String'].convert_to(syntax, [str(prop.Default)])

                # check for multivalue, mandatory and unique definition
                multivalue = bool(load(prop, "MultiValue", False))
                unique = bool(load(prop, "Unique", False))
                mandatory = bool(load(prop, "Mandatory", False))
                readonly = bool(load(prop, "ReadOnly", False))
                case_sensitive = bool(load(prop, "CaseSensitive", False))
                foreign = bool(load(prop, "Foreign", False))

                # Check for property dependencies
                depends_on = []
                if "DependsOn" in prop.__dict__:
                    for d in prop.__dict__['DependsOn'].iterchildren():
                        depends_on.append(str(d))

                # Check for valid value list
                values = None
                if "Values" in prop.__dict__:
                    values = []
                    for d in prop.__dict__['Values'].iterchildren():
                        values.append(str(d))
                    values = self.__attribute_type['String'].convert_to(syntax,values)

                # Create a new property with the given information
                props[str(prop['Name'])] =  {
                    'value': [],
                    'values': values,
                    'status': STATUS_OK,
                    'depends_on': depends_on,
                    'type': syntax,
                    'backend_type': backend_syntax,
                    'validator': validator,
                    'out_filter': out_f,
                    'in_filter': in_f,
                    'backend': [backend],
                    'in_value': [],
                    'default': default,
                    'orig_value': None,
                    'foreign': foreign,
                    'unique': unique,
                    'mandatory': mandatory,
                    'readonly': readonly,
                    'case_sensitive': case_sensitive,
                    'multivalue': multivalue,
                    'blocked_by': blocked_by}

        # Validate the properties 'depends_on' and 'blocked_by' lists
        for pname in props:

            # Blocked by
            for bentry in props[pname]['blocked_by']:

                # Does the blocking property exists?
                if bentry['name'] not in props:
                    raise FactoryException("Property '%s' cannot be blocked by a non existing property '%s', please check the XML definition!" % (
                            pname, bentry['name']))

                # Convert the blocking condition to its expected value-type
                syntax = props[bentry['name']]['type']
                bentry['value'] = self.__attribute_type['String'].convert_to(syntax, [bentry['value']])[0]

            # Depends on
            for dentry in props[pname]['depends_on']:
                if dentry not in props:
                    raise FactoryException("Property '%s' cannot depend on non existing property '%s', please check the XML definition!" % (
                            pname, dentry))

        # Build up a list of callable methods
        if 'Methods' in classr.__dict__:
            for method in classr['Methods']['Method']:

                # Extract method information out of the xml tag
                methodName = str(method['Name'])
                command = str(method['Command'])

                # Get the list of method parameters
                mParams = []
                if 'MethodParameters' in method.__dict__:

                    # Todo: Check type of the property and handle the
                    # default value.

                    for param in method['MethodParameters']['MethodParameter']:
                        pName = str(param['Name'])
                        pType = str(param['Type'])
                        pRequired = bool(load(param, "Required", False))
                        pDefault = str(load(param, "Default"))
                        mParams.append( (pName, pType, pRequired, pDefault), )

                # Get the list of command parameters
                cParams = []
                if 'CommandParameters' in method.__dict__:
                    for param in method['CommandParameters']['Value']:
                        cParams.append(str(param))

                # Now add the method to the object
                def funk(*args, **kwargs):

                    # Convert all given parameters into named arguments
                    # The eases up things a lot.
                    cnt = 0
                    arguments = {}
                    for mParam in mParams:
                        mName, mType, mRequired, mDefault = mParam
                        if mName in kwargs:
                            arguments[mName] = kwargs[mName]
                        elif cnt < len(args):
                            arguments[mName] = args[cnt]
                        elif mDefault:
                            arguments[mName] = mDefault
                        else:
                            raise FactoryException("Missing parameter '%s'!" % mName)

                        # Convert value to its required type.
                        arguments[mName] = self.__attribute_type['String'].convert_to(mType,[arguments[mName]])[0]
                        cnt = cnt + 1

                    # Build the command-parameter list.
                    # Collect all property values of this object to be able to fill in
                    # placeholders in command-parameters later.
                    propList = {}
                    for key in props:
                        if props[key]['value']:
                            propList[key] = props[key]['value'][0]
                        else:
                            propList[key] = None

                    # Add method-parameters passed to this method.
                    for entry in arguments:
                        propList[entry] = arguments[entry]

                    # Fill in the placeholders of the command-parameters now.
                    parmList = []
                    for value in cParams:
                        if value in propList:
                            parmList.append(propList[value])
                        else:
                            raise FactoryException("Method '%s' depends on unknown attribute '%s'!" % (command, value))

                    # Dispatch message
                    try:
                        cr = PluginRegistry.getInstance('CommandRegistry')
                    except:
                        raise FactoryException("The command registry could not be found, are you running things manually?!")

                    return(cr.dispatch(command, *parmList))

                # Append the method to the list of registered methods for this
                # object
                self.log.debug("adding method: '%s'" % (methodName, ))
                methods[methodName] = {'ref': funk}

        # Set properties and methods for this object.
        setattr(klass, '__properties', props)
        setattr(klass, '__methods', methods)
        return klass

    def __build_filter(self, element, out=None):
        """
        Attributes of objects can be filtered using in- and out-filters.
        These filters can manipulate the raw-values while they are read form
        the backend or they can manipulate values that have to be written to
        the backend.

        This method converts the read XML filter-elements of the defintion into
        a process lists. This list can then be easily executed line by line for
        each property, using the method:

        :meth:`clacks.agent.objects.factory.Object.__processFilter`

        """

        # Parse each <FilterChain>, <Condition>, <ConditionChain>
        out = {}
        for el in element.iterchildren():
            if el.tag == "{http://www.gonicus.de/Objects}FilterChain":
                out = self.__handleFilterChain(el, out)
            elif  el.tag == "{http://www.gonicus.de/Objects}Condition":
                out = self.__handleCondition(el, out)
            elif  el.tag == "{http://www.gonicus.de/Objects}ConditionOperator":
                out = self.__handleConditionOperator(el, out)

        return out

    def __handleFilterChain(self, element, out=None):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'FilterChain' element is handled here.

        Occurrence: OutFilter->FilterChain
        """
        if not out:
            out = {}

        # FilterChains can contain muliple "FilterEntry" tags.
        # But at least one.
        # Here we forward these elements to their handler.
        for el in element.iterchildren():
            if el.tag == "{http://www.gonicus.de/Objects}FilterEntry":
                out = self.__handleFilterEntry(el, out)
        return out

    def __handleFilterEntry(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'FilterEntry' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry
        """

        # FilterEntries contain a "Filter" OR a "Choice" tag.
        # Here we forward the elements to their handler.
        for el in element.iterchildren():
            if el.tag == "{http://www.gonicus.de/Objects}Filter":
                out = self.__handleFilter(el, out)
            elif el.tag == "{http://www.gonicus.de/Objects}Choice":
                out = self.__handleChoice(el, out)
        return out

    def __handleFilter(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'Filter' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Filter
        """

        # Get the <Name> and the <Param> element values to be able
        # to create a process list entry.
        name = str(element.__dict__['Name'])
        params = []
        for entry in element.iterchildren():
            if entry.tag == "{http://www.gonicus.de/Objects}Param":
                params.append(entry.text)

        # Attach the collected filter and parameter value to the process list.
        cnt = len(out) + 1
        out[cnt] = {'filter': get_filter(name)(self), 'params': params}
        return out

    def __handleChoice(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'Choice' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Choice
        """

        # We just forward <When> tags to their handler.
        for el in element.iterchildren():
            if el.tag == "{http://www.gonicus.de/Objects}When":
                out = self.__handleWhen(el, out)
        return(out)

    def __handleWhen(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'When' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Choice->When
        """

        # (<When> tags contain a <ConditionChain>, a <FilterChain> tag and
        # an optional <Else> tag.
        #  The <FilterChain> is only executed when the <ConditionChain> matches
        #  the given values.)

        # Forward the tags to their correct handler.
        filterChain = {}
        elseChain = {}
        for el in element.iterchildren():
            if el.tag == "{http://www.gonicus.de/Objects}ConditionChain":
                out = self.__handleConditionChain(el, out)
            if el.tag == "{http://www.gonicus.de/Objects}FilterChain":
                filterChain = self.__handleFilterChain(el, filterChain)
            elif el.tag == "{http://www.gonicus.de/Objects}Else":
                elseChain = self.__handleElse(el, elseChain)

        # Collect jump points
        cnt = len(out)
        match = cnt + 2
        endMatch = match + len(filterChain)
        noMatch = endMatch + 1
        endNoMatch = noMatch + len(elseChain)

        # Add jump point for this condition
        cnt = len(out)
        out[cnt + 1] = {'jump': 'conditional', 'onTrue': match, 'onFalse': noMatch}

        # Add the <FilterChain> process.
        cnt = len(out)
        for entry in filterChain:
            cnt = cnt + 1
            out[cnt] = filterChain[entry]

        # Add jump point to jump over the else chain
        cnt = len(out)
        out[cnt + 1] = {'jump': 'non-conditional', 'to': endNoMatch}

        # Add the <Else> process.
        cnt = len(out)
        for entry in elseChain:
            cnt = cnt + 1
            out[cnt] = elseChain[entry]

        return(out)

    def __handleElse(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'Else' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Choice->Else
        """

        # Handle <FilterChain> elements of this else tree.
        for el in element.iterchildren():
            if el.tag == "{http://www.gonicus.de/Objects}FilterChain":
                out = self.__handleFilterChain(el, out)

        return out

    def __handleConditionChain(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'ConditionChain' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Choice->When->ConditionChain
        """

        # Forward <Condition> tags to their handler.
        for el in element.iterchildren():
            if el.tag == "{http://www.gonicus.de/Objects}Condition":
                out = self.__handleCondition(el, out)
            elif el.tag == "{http://www.gonicus.de/Objects}ConditionOperator":
                out = self.__handleConditionOperator(el, out)

        return out

    def __handleConditionOperator(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'ConditionOperator' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Choice->When->ConditionChain->ConditionOperator
        """

        # Forward <Left and <RightConditionChains> to the ConditionChain handler.
        out = self.__handleConditionChain(element.__dict__['LeftConditionChain'], out)
        out = self.__handleConditionChain(element.__dict__['RightConditionChain'], out)

        # Append operator
        cnt = len(out)
        if element.__dict__['Operator'] == "or":
            out[cnt + 1] = {'operator': get_operator('Or')(self)}
        else:
            out[cnt + 1] = {'operator': get_operator('And')(self)}

        return out

    def __handleCondition(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'Condition' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Choice->When->ConditionChain->Condition
        """

        # Get the condition name and the parameters to use.
        # The name of the condition specifies which ElementComparator
        # we schould use.
        name = str(element.__dict__['Name'])
        params = []
        for entry in element.iterchildren():
            if entry.tag == "{http://www.gonicus.de/Objects}Param":
                params.append(entry.text)

        # Append the condition to the process list.
        cnt = len(out) + 1
        out[cnt] = {'condition': get_comparator(name)(self), 'params': params}
        return(out)

    @staticmethod
    def getInstance():
        if not ObjectFactory.__instance:
            ObjectFactory.__instance = ObjectFactory()

        return ObjectFactory.__instance

    def __get_backend_parameters(self, obj):
        backend_attrs = None

        if "BackendParameters" in obj.__dict__:
            for bp in obj.BackendParameters.Backend:
                if str(bp) == obj.Backend:
                    backend_attrs = bp.attrib
                    break

        return backend_attrs

    def getXMLObjectSchema(self, asString=False):
        """
        Returns a xml-schema definition that can be used to validate the
        xml-objects returned by 'asXML()'
        """
        # Transform xml-combination into a useable xml-class representation
        xmldefs = self.getXMLDefinitionsCombined()
        xslt_doc = etree.parse(pkg_resources.resource_filename('clacks.agent', 'data/xml_object_schema.xsl'))
        transform = etree.XSLT(xslt_doc)
        if not asString:
            return transform(xmldefs)
        else:
            return etree.tostring(transform(xmldefs))

