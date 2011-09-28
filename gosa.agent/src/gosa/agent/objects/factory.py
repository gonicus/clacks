# -*- coding: utf-8 -*-
"""

GOsa Object Factory
===================

Short description
^^^^^^^^^^^^^^^^^

The object factory provides access to backend-data in an object
oriented way. You can create, read, update and delete objects easily.

What object-types are avaialable is configured using XML files, these files
are located here: ``./gosa.common/src/gosa/common/data/objects/``.

Each XML file can contain multiple object definitions, with object related
information, like attributes, methods, how to store and read
objects.

(For a detailed documentation of the of XML files, please have a look at the
./doc directory)

A python meta-class will be created for each object-definition.
Those meta-classes will then be used to instantiate a new python object,
which will then provide the defined attributes, methods, aso.

Here are some examples on how to instatiate on new object:

>>> from gosa.agent.objects import GOsaObjectFactory
>>> person = f.getObject('Person', "410ad9f0-c4c0-11e0-962b-0800200c9a66")
>>> print person->sn
>>> person->sn = "Surname"
>>> person->commit()


"""

import pkg_resources
import os
import time
import datetime
import re
from lxml import etree, objectify
from gosa.common import Environment
from gosa.agent.objects.filter import get_filter
from gosa.agent.objects.backend.registry import ObjectBackendRegistry, load
from gosa.agent.objects.comparator import get_comparator
from gosa.agent.objects.operator import get_operator

# Map XML base types to python values
TYPE_MAP = {
        'Boolean': bool,
        'String': str,
        'UnicodeString': unicode,
        'Integer': int,
        'Timestamp': time.time,
        'Date': datetime.date,
        'Binary': None,
        'Dictionary': dict,
        'List': list,
        }

TYPE_MAP_REV = dict([(TYPE_MAP[k], k) for k in TYPE_MAP.keys()])

# Status
STATUS_OK = 0
STATUS_CHANGED = 1


class GOsaObjectFactory(object):
    """
    This class reads GOsa-object defintions and generates python-meta classes
    for each object, which can then be instantiated using
    :meth:`gosa.agent.objects.factory.GOsaObjectFactory.getObject`.
    """
    __xml_defs = {}
    __classes = {}
    __var_regex = re.compile('^[a-z_][a-z0-9\-_]*$', re.IGNORECASE)

    def __init__(self, path):
        self.env = Environment.getInstance()

        # Initialize parser
        #pylint: disable=E1101
        schema_path = pkg_resources.resource_filename('gosa.agent', 'data/objects/object.xsd')
        schema_doc = open(schema_path).read()
        schema_root = etree.XML(schema_doc)
        schema = etree.XMLSchema(schema_root)
        self.__parser = objectify.makeparser(schema=schema)

        # Load and parse schema
        self.loadSchema(path)

#----------------------------------------------------------------------------------------

    #@Command()
    def getObject(self, name, *args, **kwargs):
        """
        Returns a GOsa-object instance.

        e.g.:

        >>> person = f.getObject('Person', "410ad9f0-c4c0-11e0-962b-0800200c9a66")

        """
        if not name in self.__classes:
            self.__classes[name] = self.__build_class(name)

        return self.__classes[name](*args, **kwargs)

    #@Command()
    def createObject(self, name, *args, **kwargs):
        #TODO
        pass

    #@Command()
    def removeObject(self, name, uuid, recursive=False):
        #TODO
        pass

    #@Command()
    def getObjectExtensions(self, name, *args, **kwargs):
        #TODO
        pass

    #@Command()
    def getObjectExtension(self, name, *args, **kwargs):
        #TODO
        pass

    #@Command()
    def createObjectExtension(self, name, *args, **kwargs):
        #TODO
        pass

    #@Command()
    def removeObjectExtension(self, name, uuid):
        #TODO
        pass

#----------------------------------------------------------------------------------------

    def loadSchema(self, path):
        """
        This method reads all gosa-object defintion files and then calls
        :meth:`gosa.agent.objects.factory.GOsaObjectFactory.getObject`
        to initiate the parsing into meta-classes for each file.

        These meta-classes are used for object instantiation later.

        """
        #pylint: disable=E1101
        path = pkg_resources.resource_filename('gosa.agent', 'data/objects')

        # Include built in schema
        for f in [n for n in os.listdir(path) if n.endswith(os.extsep + 'xml')]:
            self.__parse_schema(os.path.join(path, f))

        # Include additional schema configuration
        path = os.path.join(self.env.config.getBaseDir(), 'schema')
        if os.path.isdir(path):
            for f in [n for n in os.listdir(path) if n.endswith(os.extsep + 'xml')]:
                self.__parse_schema(os.path.join(path, f))

    def __parse_schema(self, path):
        """
        Parses a schema file using the
        :meth:`gosa.agent.objects.factory.GOsaObjectFactory.__parser`
        method.
        """
        try:
            xml = objectify.fromstring(open(path).read(), self.__parser)
            self.__xml_defs[str(xml.Object['Name'][0])] = xml

        except etree.XMLSyntaxError as e:
            print "Error loading: %s, %s", path, e
            exit()

    def __build_class(self, name):
        """
        This method builds a meta-class for each object defintion read from the
        xml defintion files.

        It uses a base-meta-class which will be extended by the define
        attributes and mehtods of the object.

        The final meta-class will be stored and can then be requested using:
        :meth:`gosa.agent.objects.factory.GOsaObjectFactory.getObject`
        """
        class klass(GOsaObject):

            #pylint: disable=E0213
            def __init__(me, *args, **kwargs):
                GOsaObject.__init__(me, *args, **kwargs)

            #pylint: disable=E0213
            def __setattr__(me, name, value):
                me._setattr_(name, value)

            #pylint: disable=E0213
            def __getattr__(me, name):
                return me._getattr_(name)

            #pylint: disable=E0213
            def __del__(me):
                me._del_()

        # Tweak name to the new target
        setattr(klass, '__name__', name)
        setattr(klass, '_backend', str(self.__xml_defs[name].Object.DefaultBackend))

        # Prepare property and method list.
        classr = self.__xml_defs[name].Object
        props = {}
        methods = {}

        # Add documentation if available
        if 'description' in classr:
            setattr(klass, '__doc__', str(classr['description']))

        # Check for a default backend
        defaultBackend = None
        if "DefaultBackend" in classr.__dict__:
            defaultBackend = str(classr.DefaultBackend)

        # Append attributes
        for prop in classr['Attributes']['Attribute']:

            # Read backend definition per property (if it exists)
            out_b = defaultBackend
            in_b = defaultBackend
            if "Backend" in prop.__dict__:
                out_b =  str(prop.Backend)
                in_b =  str(prop.Backend)

            # Do we have an output filter definition?
            out_f =  []
            if "OutFilter" in prop.__dict__:
                for entry in  prop['OutFilter'].iterchildren():
                    out_f.append(self.__handleFilterChain(entry))

            # Do we have a input filter definition?
            in_f =  []
            if "InFilter" in prop.__dict__:
                for entry in  prop['InFilter'].iterchildren():
                    in_f.append(self.__handleFilterChain(entry))

            # We require at least one backend information tag
            if not in_b:
                raise Exception("Cannot detect a valid input backend for "
                        "attribute %s!" % (prop['Name'],))
            if not out_b:
                raise Exception("Cannot detect a valid output backend for "
                        "attribute %s!" % (prop['Name'],))

            # Read and build up validators
            validator =  None
            if "Validators" in prop.__dict__:
                validator = self.__build_filter(prop['Validators'])

            # Read the properties syntax
            syntax = str(prop['Syntax'])

            # check for multivalue definition
            multivalue = bool(prop['MultiValue']) if "MultiValue" in prop.__dict__ else False

            # Check for property dependencies
            dependsOn = []
            if "DependsOn" in prop.__dict__:
                for d in prop.__dict__['DependsOn'].iterchildren():
                    dependsOn.append(str(d))

            props[str(prop['Name'])] = {
                    'value': None,
                    'in_value': None,
                    'in_name': None,
                    'orig': None,
                    'status': STATUS_OK,
                    'dependsOn': dependsOn,
                    'type': TYPE_MAP[syntax],
                    'syntax': syntax,
                    'validator': validator,
                    'out_filter': out_f,
                    'out_backend': out_b,
                    'in_filter': in_f,
                    'in_backend': in_b,
                    'multivalue': multivalue}

        # Build up a list of callable methods
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
                    pRequired = bool(param['Required']) if 'Required' in param.__dict__ else False
                    pDefault = str(param['Default']) if 'Default' in param.__dict__ else None
                    mParams.append( (pName, pType, pRequired, pDefault), )

            # Get the list of command parameters
            cParams = []
            if 'CommandParameters' in method.__dict__:
                for param in method['CommandParameters']['CommandParameter']:
                    cParams.append(str(param['Value']))

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
                        arguments[mName] = TYPE_MAP[mType](mDefault)
                    else:
                        raise(Exception("Missing parameter '%s'!" % mName))

                    # Ensure that the correct parameter type was given.
                    if TYPE_MAP[mType] != type(arguments[mName]):
                        raise(Exception("Invalid parameter type given for '%s', expected "
                            "'%s' but received '%s'!" % (mName,
                                TYPE_MAP[mType],type(arguments[mName]))))

                    cnt = cnt + 1

                # Build the command-parameter list.
                # Collect all property values of this GOsa-object to be able to fill in
                # placeholders in command-parameters later.
                propList = {}
                for key in props:
                    propList[key] = props[key]['value']

                # Add method-parameters passed to this method.
                for entry in arguments:
                    propList[entry] = arguments[entry]

                # Fill in the placeholders of the command-parameters now.
                parameterList = []
                for value in cParams:
                    try:
                        value = value % propList
                    except:
                        raise(Exception("Cannot call method '%s', error while filling "
                            " in placeholders! Error processing: %s!" %
                            (methodName, value)))

                    parameterList.append(value)

                #TODO: Execute real-stuff later
                print "Calling class method:", parameterList, command

            # Append the method to the list of registered methods for this
            # object
            methods[methodName] = {'ref': funk}

        # Set properties and methods for this object.
        setattr(klass, '__properties', props)
        setattr(klass, '__methods', methods)

        return klass


    def __build_filter(self, element, out=None):
        """
        Attributes of GOsa objects can be filtered using in- and out-filters.
        These filters can manipulate the raw-values while they are read form
        the backend or they can manipulate values that have to be written to
        the backend.

        This method converts the read XML filter-elements of the defintion into
        a process lists. This list can then be easily executed line by line for
        each property, using the method:

        :meth:`gosa.agent.objects.factory.GOsaObject.__processFilter`

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


class GOsaObject(object):
    """
    This class is the base class for all GOsa-objects.

    It contains getter and setter methods for the object
    attributes and it is able to initialize itself by reading data from
    backends.

    It also contains the ability to execute the in- and out-filters for the
    object properties.

    All meta-classes for GOsa-objects, created by the XML defintions, will inherit this class.

    """
    _reg = None
    _backend = None
    uuid = None

    def __init__(self, dn=None):

        # Initialize object using a dn
        if dn:
            self._read(dn)

    def _read(self, dn):
        """
        This method tries to initialize a GOsa-object instance by reading data
        from the defined backend.

        Attributes will be grouped by their backend to ensure that only one
        request per backend will be performed.

        """

        # Instantiate Backend-Registry
        self._reg = ObjectBackendRegistry.getInstance()
        self.uuid = self._reg.dn2uuid(self._backend, dn)

        # Group attributes by Backend
        propsByBackend = {}
        props = getattr(self, '__properties')
        for key in props:

            # Initialize an empty array for each backend
            if props[key]['in_backend'] not in propsByBackend:
                propsByBackend[props[key]['in_backend']] = []

            # Append property
            propsByBackend[props[key]['in_backend']].append(key)

        # Load attributes for each backend.
        # And then assign the values to the properties.
        obj = self
        for backend in propsByBackend:

            try:
                # Create a dictionary with all attributes we want to fetch
                # {attribute_name: type, name: type}
                info = dict([(k, TYPE_MAP_REV[props[key]['type']]) for k in propsByBackend[backend]])
                attrs = load(obj, info, backend)
            except ValueError:
                print "Error reading property: %s!" % (backend,)
                continue

            # Assign fetched value to the properties.
            for key in propsByBackend[backend]:

                # Assign property
                if 'MultiValue' in props[key] and props[key]['MultiValue']:
                    value = attrs[key]
                else:
                    value = attrs[key][0]

                props[key]['value'] = value

                # Keep original values, they may be overwritten in the in-filters.
                props[key]['in_value'] = value
                props[key]['in_value'] = key

            # Once we've loaded all properties from the backend, execute the
            # in-filters.
            for key in propsByBackend[backend]:

                # Execute defined in-filters.
                if len(props[key]['in_filter']):

                    value = props[key]['value']
                    for in_f in props[key]['in_filter']:
                        valDict = {key: {
                                'backend': props[key]['in_backend'],
                                'value': value,
                                'type': props[key]['type']}}
                        valDict = self.__processFilter(in_f, key, valDict)

                        # Check if the in-filter returned a valid result.
                        # In-filters do not support property name manipulation
                        #if key not in valDict or len(valDict) != 1:
                        #    raise Exception("Property name manipulation not allowed for in-filters! "
                        #            "Check in-filter for property '%s'!" % key)

                        # Assign filter results
                        for key in valDict:
                            if key not in props:
                                props[key] = {
                                    'value':  valDict[key]['value'],
                                    'in_value': None,
                                    'in_name': None,
                                    'orig': None,
                                    'status': STATUS_OK,
                                    'dependsOn': [],
                                    'type': valDict[key]['type'],
                                    'syntax': None,
                                    'validator': None,
                                    'out_filter': None,
                                    'out_backend': valDict[key]['backend'],
                                    'in_filter': None,
                                    'in_backend': valDict[key]['backend'],
                                    'multivalue': False}

                # Keep the initial value
                props[key]['old'] = props[key]['value']

    def _setattr_(self, name, value):

        """
        This is the setter method for GOsa-object attributes.
        Each given attribute value is validated with the given set of
        validators.
        """

        # Store non property values
        try:
            object.__getattribute__(self, name)
            self.__dict__[name] = value
            return
        except AttributeError:
            pass

        # Try to save as property value
        props = getattr(self, '__properties')
        if name in props:
            current = props[name]['value']

            # Run type check
            if props[name]['type'] and not issubclass(type(value), props[name]['type']):
                raise TypeError("cannot assign value '%s'(%s) to property '%s'(%s)" % (
                    value, type(value).__name__,
                    name, props[name]['syntax']))

            # Validate value
            if props[name]['validator']:
                res, error = self.__processValidator(props[name]['validator'],
                        name, value)
                if not res:
                    print "%s" % (error)
                    return

            # Set the new value
            props[name]['value'] = value

            # Update status if there's a change
            if current != props[name]['value'] and props[name]['status'] != STATUS_CHANGED:
                props[name]['status'] = STATUS_CHANGED
                props[name]['old'] = current

        else:
            raise AttributeError("no such property '%s'" % name)

    def _getattr_(self, name):
        """
        The getter method GOsa-object attributes.

        (It differentiates between GOsa-object attributes and class-members)
        """
        props = getattr(self, '__properties')
        methods = getattr(self, '__methods')

        if name in props:
            return props[name]['value']

        elif name in methods:
            return methods[name]['ref']

        else:
            raise AttributeError("no such property '%s'" % name)

    def getAttrType(self, name):
        """
        Return the type of a given GOsa-object attribute.
        """

        props = getattr(self, '__properties')
        if name in props:
            return props[name]['type']

        raise AttributeError("no such property '%s'" % name)

    def commit(self):
        """
        Commits changes of an GOsa-object to the corresponding backends.
        """

        props = getattr(self, '__properties')

        # Collect values by store and process the property filters
        toStore = {}
        for key in props:

            # Adapt status from dependent properties.
            for propname in props[key]['dependsOn']:
                props[key]['status'] |= props[propname]['status'] & STATUS_CHANGED

            # Do not save untouched values
            if not props[key]['status'] & STATUS_CHANGED:
                continue

            # Get the new value for the property and execute the out-filter
            value = props[key]['value']
            new_key = key

            # Process each and every out-filter with a clean set of input values,
            #  to avoid that return-values overwrite themselves.
            if len(props[key]['out_filter']):
                for out_f in props[key]['out_filter']:
                    valDict = {key: {
                            'backend': props[key]['out_backend'],
                            'value': props[key]['value'],
                            'type': TYPE_MAP_REV[props[key]['type']]}}

                    valDict = self.__processFilter(out_f, key, valDict)

                    # Collect properties by backend
                    for prop_key in valDict:
                        be = valDict[prop_key]['backend']

                        if not be in toStore:
                            toStore[be] = {}
                        toStore[be][prop_key] = valDict[prop_key]
            else:

                # Collect properties by backend
                be = props[key]['out_backend']
                if not be in toStore:
                    toStore[be] = {}
                toStore[be][key] = {
                    'backend': be,
                    'value': props[key]['value'],
                    'type': TYPE_MAP_REV[props[key]['type']]}

        print "\n\n---- Saving ----"
        for store in toStore:
            print " |-> %s (Backend)" % store
            for entry in toStore[store]:
                print "   |-> %s: " % entry, toStore[store][entry]

    def revert(self):
        """
        Reverts all changes made to this object since it was loaded.
        """
        props = getattr(self, '__properties')
        for key in props:
            props[key]['value'] = props[key]['in_value']

    def __processValidator(self, fltr, key, value):
        """
        This method processes a given process-list (fltr) for a given property (prop).
        And return TRUE if the value matches the validator set and FALSE if
        not.
        """

        # This is our process-line pointer it points to the process-list line
        #  we're executing at the moment
        lptr = 0

        # Our filter result stack
        stack = list()

        # Process the list till we reach the end..
        lasterrmsg = ""
        errormsgs = []
        while (lptr + 1) in fltr:

            # Get the current line and increase the process list pointer.
            lptr = lptr + 1
            curline = fltr[lptr]

            # A condition matches for something and returns a boolean value.
            # We'll put this value on the stack for later use.
            if 'condition' in curline:

                # Build up argument list
                args = [key, value] + curline['params']

                # Process condition and keep results
                errors = []
                named = {'errors': errors}
                v = (curline['condition']).process(*args, **named)
                stack.append(v)
                if not v:
                    if len(errors):
                        lasterrmsg =  errors.pop()

            # A comparator compares two values from the stack and then returns a single
            #  boolean value.
            elif 'operator' in curline:
                v1 = stack.pop()
                v2 = stack.pop()
                res = (curline['operator']).process(v1, v2)
                stack.append(res)

                # Add last error message
                if not res:
                    errormsgs.append(lasterrmsg)
                    lasterrmsg = ""

        # Attach last error message
        res = stack.pop()
        if not res and lasterrmsg != "":
            errormsgs.append(lasterrmsg)

        return res, errormsgs

    def __processFilter(self, fltr, key, prop):
        """
        This method processes a given process-list (fltr) for a given property (prop).
        For example: When a property has to be stored in the backend, it will
         run through the out-filter-process-list and thus will be transformed into a storable
         key, value pair.
        """

        # Search for replaceable patterns in the process-list.
        fltr = self.__fillInPlaceholders(fltr)

        # This is our process-line pointer it points to the process-list line
        #  we're executing at the moment
        lptr = 0

        # Our filter result stack
        stack = list()

        # Process the list till we reach the end..
        while (lptr + 1) in fltr:

            # Get the current line and increase the process list pointer.
            lptr = lptr + 1
            curline = fltr[lptr]

            # A filter is used to manipulate the 'value' or the 'key' or maybe both.
            if 'filter' in curline:

                # Build up argument list
                args = [self, key, prop]
                for entry in curline['params']:
                    args.append(entry)

                # Process filter and keep results
                key, prop = (curline['filter']).process(*args)

                # Ensure that the processed data is still valid.
                # Filter may mess things up and then the next cannot process correctly.
                if (key not in prop):
                    fname = type(curline['filter']).__name__
                    raise Exception("Filter '%s' returned invalid key property key '%s'!" % (fname, key))

                # Check if the filter returned all expected property values.
                for pk in prop:
                    if not all(k in prop[pk] for k in ('backend', 'value', 'type')):
                        fname = type(curline['filter']).__name__
                        missing = ", ".join(set(['backend', 'value', 'type']) - set(prop[pk].keys()))
                        raise Exception("Filter '%s' does not return all expected property values! '%s' missing." % (fname, missing))

            # A condition matches for something and returns a boolean value.
            # We'll put this value on the stack for later use.
            elif 'condition' in curline:

                # Build up argument list
                args = [key] + curline['params']

                # Process condition and keep results
                stack.append((curline['condition']).process(*args))

            # Handle jump, for example if a condition has failed, jump over its filter-chain.
            elif 'jump' in curline:

                # Jump to <line> -1 because we will increase the line ptr later.
                if curline['jump'] == 'conditional':
                    if stack.pop():
                        lptr = curline['onTrue'] - 1
                    else:
                        lptr = curline['onFalse'] - 1
                else:
                    lptr = curline['to'] - 1

            # A comparator compares two values from the stack and then returns a single
            #  boolean value.
            elif 'operator' in curline:
                stack.append((curline['operator']).process(stack.pop(), stack.pop()))

        return prop

    def __fillInPlaceholders(self, fltr):
        """
        This method fill in placeholder into in- and out-filters.
        """

        # Collect all property values
        propList = {}
        props = getattr(self, '__properties')
        for key in props:
            propList[key] =  props[key]['value']

        # An inline function which replaces format string tokens
        def _placeHolder(x):
            for name in propList:
                x = x % propList
            return (x)

        # Walk trough each line of the process list an replace placeholders.
        for line in fltr:
            if 'params' in fltr[line]:
                fltr[line]['params'] = map(_placeHolder,
                        fltr[line]['params'])
        return fltr

    def delete(self):
        """
        Removes this object.
        """
        #TODO
        print "--> built in delete method"

    def _del_(self):
        """
        Internal cleanup method ...
        """
        #TODO
        print "--> cleanup"
