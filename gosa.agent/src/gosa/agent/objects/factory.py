# -*- coding: utf-8 -*-
import pkg_resources
import os
import time
import datetime
import re
from lxml import etree, objectify
from gosa.agent.objects.backend.registry import ObjectBackendRegistry, loadAttrs
from gosa.agent.objects.filter import get_filter
from gosa.agent.objects.comparator import get_comparator
from gosa.agent.objects.operator import get_operator


# Map XML base types to python values
TYPE_MAP = {
        'Boolean': bool,
        'String': unicode,
        'Integer': int,
        'Timestamp': time.time,
        'Date': datetime.date,
        'Binary': None,
        'Dictionary': dict,
        'List': list,
        }

# Status
STATUS_OK = 0
STATUS_CHANGED = 1


class GOsaObjectFactory(object):

    __xml_defs = {}
    __classes = {}
    __var_regex = re.compile('^[a-z_][a-z0-9\-_]*$', re.IGNORECASE)

    def __init__(self, path):
        # Initialize parser
        schema_path = pkg_resources.resource_filename('gosa.common', 'data/objects/object.xsd')
        schema_doc = open(schema_path).read()
        schema_root = etree.XML(schema_doc)
        schema = etree.XMLSchema(schema_root)
        self.__parser = objectify.makeparser(schema=schema)

        # Load and parse schema
        self.load_schema(path)

    def load_schema(self, path):
        path = pkg_resources.resource_filename('gosa.common', 'data/objects')

        # Look on path and check for xml files
        for f in [n for n in os.listdir(path) if n.endswith(os.extsep + 'xml')]:
            self.__parse_schema(os.path.join(path, f))

    def __parse_schema(self, path):
        print "Loading %s..." % path

        # Load and validate objects
        try:
            xml = objectify.fromstring(open(path).read(), self.__parser)
            self.__xml_defs[str(xml.Object['Name'][0])] = xml

        except etree.XMLSyntaxError as e:
            print "Error:", e
            exit()

    #@Command()
    def getObjectInstance(self, name, *args, **kwargs):
        if not name in self.__classes:
            self.__classes[name] = self.__build_class(name)

        return self.__classes[name](*args, **kwargs)

    def __build_class(self, name):
        class klass(GOsaObject):

            def __init__(me, *args, **kwargs):
                GOsaObject.__init__(me, *args, **kwargs)

            def __setattr__(me, name, value):
                me._setattr_(name, value)

            def __getattr__(me, name):
                return me._getattr_(name)

            def __del__(me):
                me._del_()

        # Tweak name to the new target
        setattr(klass, '__name__', name)
        setattr(klass, '_backend', str(self.__xml_defs[name].Object.DefaultBackend))

        # What kind of properties do we have?
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

        for prop in classr['Attributes']['Attribute']:

            # Read backend definitions per property (if they exists)
            out_b = defaultBackend
            in_b = defaultBackend
            if "Backend" in prop.__dict__:
                out_b =  str(prop.Backend)
                in_b =  str(prop.Backend)

            # Do we have an output filter definition?
            out_f =  None
            if "OutFilter" in prop.__dict__:
                out_f = self.__build_filter(prop['OutFilter'])
                if 'Backend' in prop['OutFilter'].__dict__:
                    out_b = str(prop['OutFilter']['Backend'])

            # Do we have a input filter definition?
            in_f =  None
            if "InFilter" in prop.__dict__:
                in_f = self.__build_filter(prop['InFilter'])
                if 'Backend' in prop['InFilter'].__dict__:
                    in_b = str(prop['InFilter']['Backend'])

            # We require at least one backend information tag
            if not in_b:
                raise Exception("Cannot detect a valid input backend for "
                        "attribute %s!" % (prop['Name'],))
            if not out_b:
                raise Exception(_("Cannot detect a valid output backend for "
                        "attribute %s!") % (prop['Name'],))

            # Read for a validator
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
                    'name': str(prop['Name']),
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

            #-----------------
            #validators....
            #-----------------

            #TODO: no exec plz
            #for method in classr['Methods']['Method']:
            #    name = str(method['Name'])

            #    def funk(*args, **kwargs):
            #        variables = {'title': args[0], 'message': args[1]}
            #        self.__exec(unicode(str(method['Code']).strip()), variables)

            #    methods[name] = {
            #            'ref': funk}

        #except KeyError:
        #    pass

        setattr(klass, '__properties', props)
        setattr(klass, '__methods', methods)

        return klass


    def __build_filter(self, element, out=None):
        """
        Converts an XML etree element into a process list.
        This list can then be easily executed line by line for each property.
        """

        # Parse each <FilterChain>
        out = {}
        for el in element.iterchildren():
            if el.tag == "{http://www.gonicus.de/Objects}FilterChain":
                out = self.__handleFilterChain(el, out)
            elif  el.tag == "{http://www.gonicus.de/Objects}Condition":
                out = self.__handleCondition(el, out)
            elif  el.tag == "{http://www.gonicus.de/Objects}ConditionOperator":
                out = self.__handleConditionOperator(el, out)

        return out

    def __handleFilterChain(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'FilterChain' element is handled here.

        Occurrence: OutFilter->FilterChain
        """

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
    # This may contain some useful stuff later on
    _reg = None
    _backend = None
    uuid = None

    def __init__(self, dn=None):

        # Initialize object using a dn
        if dn:
            self._read(dn)

    def _read(self, dn):

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
                attrs = loadAttrs(obj, propsByBackend[backend], backend)
            except ValueError as e:
                print "<<<<<<<<<<< Invalid Backend %s >>>>>>>>>>>>" % (backend,)
                continue

            # Assign fetched value to the properties.
            for key in propsByBackend[backend]:

                # Assign property
                if 'MultiValue' in props[key] and props[key]['MultiValue']:
                    value = {key: attrs[key]}
                else:
                    value = {key: attrs[key][0]}
                props[key]['value'] = value

                # If we've got an in-filter defintion then process it now.
                if props[key]['in_filter']:
                    new_key, value = self.__processFilter(props[key]['in_filter'], props[key])

                    # Update the key value if necessary
                    if key != new_key:
                        props[new_key] = props[key]
                        del(props[key])
                        key = new_key

                    # Update the value
                    props[key]['value'] = value

                # Keep the initial value
                props[key]['old'] = props[key]['value']

    def _setattr_(self, name, value):

        # Store non property values
        try:
            object.__getattribute__(self, name)
            self.__dict__[name] = value
            return
        except:
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
            props[name]['value'] = {name: value}

            # Update status if there's a change
            if current != props[name]['value'] and props[name]['status'] != STATUS_CHANGED:
                props[name]['status'] = STATUS_CHANGED
                props[name]['old'] = current

        else:
            raise AttributeError("no such property '%s'" % name)

    def _getattr_(self, name):
        props = getattr(self, '__properties')
        methods = getattr(self, '__methods')

        if name in props:
            return props[name]['value']

        elif name in methods:
            return methods[name]['ref']

        else:
            raise AttributeError("no such property '%s'" % name)

    def _del_(self):
        print "--> cleanup"

    def getAttrType(self, name):
        props = getattr(self, '__properties')
        if name in props:
            return props[name]['type']

        raise AttributeError("no such property '%s'" % name)

    def commit(self):
        props = getattr(self, '__properties')

        # Collect value by store and process the property filters
        toStore = {}
        for key in props:

            # Adapt status from dependent properties.
            for propname in props[key]['dependsOn']:
                props[key]['status'] |= props[propname]['status'] & STATUS_CHANGED

            # Do not save untouched values
            if props[key]['status'] != STATUS_CHANGED:
                continue

            # Get the new value for the property and execute the out-filter
            value = props[key]['value']
            if props[key]['out_filter']:
                key, value = self.__processFilter(props[key]['out_filter'], props[key])

            # Collect properties by backend
            if not props[key]['out_backend'] in toStore:
                toStore[props[key]['out_backend']] = {}
            toStore[props[key]['out_backend']][key] = value

        print "\n\n---- Saving ----"
        for store in toStore:
            print " |-> %s (Backend)" % store
            for entry in toStore[store]:
                print "   |-> %s: " % entry, toStore[store][entry]

    def delete(self):
        #TODO:
        print "--> built in delete method"

    def revert(self):
        print "--> built in revert method"
        #TODO:
        # Alle CHANGED attribute wieder zurück auf "old" setzen

    def __processValidator(self, fltr, key, value):
        """
        This method processes a given process-list (fltr) for a given property (prop).
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

    def __processFilter(self, fltr, prop):
        """
        This method processes a given process-list (fltr) for a given property (prop).
        For example: When a property has to be stored in the backend, it will
         run through the process list and thus will be transformed into a storable
         key, value pair.
        """

        # This is our process-line pointer it points to the process-list line
        #  we're executing at the moment
        lptr = 0

        # Read current key, value
        key = prop['name']
        value = prop['value']

        orig_value = value
        orig_key = key

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
                args = [self, key, value]
                for entry in curline['params']:
                    args.append(entry)

                # Process filter and keep results
                try:
                    key, value = (curline['filter']).process(*args)
                except Exception as e:
                    print "Abporting filter execution for:", curline
                    break

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

        return key, value