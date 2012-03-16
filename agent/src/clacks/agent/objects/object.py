# -*- coding: utf-8 -*-
import copy
import re
import zope.event
import ldap
import ldap.dn
from logging import getLogger
from zope.interface import Interface, implements
from clacks.common.components import PluginRegistry
from clacks.agent.objects.backend.registry import ObjectBackendRegistry


# Status
STATUS_OK = 0
STATUS_CHANGED = 1

_is_uuid = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')


class ObjectException(Exception):
    pass


class Object(object):
    """
    This class is the base class for all objects.

    It contains getter and setter methods for the object
    attributes and it is able to initialize itself by reading data from
    backends.

    It also contains the ability to execute the in- and out-filters for the
    object properties.

    All meta-classes for objects, created by the XML defintions, will inherit this class.

    """
    _reg = None
    _backend = None
    _mode = False
    _propsByBackend = {}
    uuid = None
    dn = None
    orig_dn = None
    log = None
    createTimestamp = None
    modifyTimestamp = None
    myProperties = None


    def __init__(self, where=None, mode="update"):

        # Instantiate Backend-Registry
        self._reg = ObjectBackendRegistry.getInstance()
        self.log = getLogger(__name__)
        self.log.debug("new object instantiated '%s'" % (type(self).__name__))

        # Group attributes by Backend
        propsByBackend = {}
        props = getattr(self, '__properties')

        self.myProperties = copy.deepcopy(props)

        for key in self.myProperties:

            # Initialize an empty array for each backend
            for be in self.myProperties[key]['backend']:
                if be not in propsByBackend:
                    propsByBackend[be] = []

                # Append property
                propsByBackend[be].append(key)

        self._propsByBackend = propsByBackend
        self._mode = mode

        # Initialize object using a DN
        if where:
            if mode == "create":
                if _is_uuid.match(where):
                    raise ValueError("create mode needs a base DN")
                self.orig_dn = self.dn = where

            else:
                self._read(where)

        # Set status to modified for attributes that do not have a value but are
        # mandatory and have a default.
        # This ensures that default values are passed to the out_filters and get saved
        # afterwards.
        # (Defaults will be passed to in-filters too, if they are not overwritten by _read())
        for key in self.myProperties:
            if not(self.myProperties[key]['value']) and self.myProperties[key]['default'] != None and \
                    len(self.myProperties[key]['default']) and self.myProperties[key]['mandatory']:
                self.myProperties[key]['status'] = STATUS_CHANGED

    def listProperties(self):
        return(self.myProperties.keys())

    def getProperties(self):
        return(copy.deepcopy(self.myProperties))

    def listMethods(self):
        methods = getattr(self, '__methods')
        return(methods.keys())

    def hasattr(self, attr):
        return attr in self.myProperties

    def _read(self, where):
        """
        This method tries to initialize a object instance by reading data
        from the defined backend.

        Attributes will be grouped by their backend to ensure that only one
        request per backend will be performed.

        """
        # Generate missing values
        if _is_uuid.match(where):
            #pylint: disable=E1101
            if self._base_object:
                self.dn = self._reg.uuid2dn(self._backend, where)
            else:
                self.dn = None

            self.uuid = where
        else:
            self.dn = where
            self.uuid = self._reg.dn2uuid(self._backend, where)

        # Get last change timestamp
        self.orig_dn = self.dn
        if self.dn:
            self.createTimestamp, self.modifyTimestamp = self._reg.get_timestamps(self._backend, self.dn)

        # Load attributes for each backend.
        # And then assign the values to the properties.
        self.log.debug("object uuid: %s" % (self.uuid))

        for backend in self._propsByBackend:

            try:
                # Create a dictionary with all attributes we want to fetch
                # {attribute_name: type, name: type}
                info = dict([(k, self.myProperties[k]['backend_type']) for k in self._propsByBackend[backend]])
                self.log.debug("loading attributes for backend '%s': %s" % (backend, str(info)))
                be = ObjectBackendRegistry.getBackend(backend)
                attrs = be.load(self.uuid, info)

            except ValueError as e:
                #raise ObjectException("Error reading properties for backend '%s'!" % (backend,))
                import traceback
                traceback.print_exc()
                exit()

            # Assign fetched value to the properties.
            for key in self._propsByBackend[backend]:

                if key not in attrs:
                    #raise ObjectException("Value for '%s' could not be read, it wasn't returned by the backend!" % (key,))
                    self.log.debug("attribute '%s' was not returned by load!" % (key))
                    continue

                # Keep original values, they may be overwritten in the in-filters.
                self.myProperties[key]['in_value'] = self.myProperties[key]['value'] = attrs[key]
                self.log.debug("%s: %s" % (key, self.myProperties[key]['value']))

        # Once we've loaded all properties from the backend, execute the
        # in-filters.
        for key in self.myProperties:

            # Skip loading in-filters for None values
            if self.myProperties[key]['value'] == None:
                self.myProperties[key]['in_value'] = self.myProperties[key]['value'] = []
                continue

            # Execute defined in-filters.
            if len(self.myProperties[key]['in_filter']):
                self.log.debug("found %s in-filter(s)  for attribute '%s'" % (str(len(self.myProperties[key]['in_filter'])),key))

                # Execute each in-filter
                for in_f in self.myProperties[key]['in_filter']:
                    self.__processFilter(in_f, key, self.myProperties)

        # Convert the received type into the target type if not done already
        #pylint: disable=E1101
        atypes = self._objectFactory.getAttributeTypes()
        for key in self.myProperties:

            # Convert values from incoming backend-type to required type
            if self.myProperties[key]['value']:
                a_type = self.myProperties[key]['type']
                be_type = self.myProperties[key]['backend_type']

                #  Convert all values to required type
                if not atypes[a_type].is_valid_value(self.myProperties[key]['value']):
                    try:
                        self.myProperties[key]['value'] = atypes[a_type].convert_from(be_type, self.myProperties[key]['value'])
                    except Exception as e:
                        self.log.error("conversion of '%s' from '%s' to type '%s' failed: %s", (key, be_type, a_type, str(e)))
                    else:
                        self.log.debug("converted '%s' from type '%s' to type '%s'!" % (key, be_type, a_type))

            # Keep the initial value
            self.myProperties[key]['last_value'] = self.myProperties[key]['orig_value'] = copy.deepcopy(self.myProperties[key]['value'])

    def _delattr_(self, name):
        """
        Deleter method for properties.
        """
        if name in self.myProperties:

            # Check if this attribute is blocked by another attribute and its value.
            for bb in  self.myProperties[name]['blocked_by']:
                if bb['value'] in self.myProperties[bb['name']]['value']:
                    raise AttributeError("This attribute is blocked by %(name)s = '%(value)s'!" % bb)

            # Do not allow to write to read-only attributes.
            if self.myProperties[name]['readonly']:
                raise AttributeError("Cannot write to readonly attribute '%s'" % name)

            # Do not allow remove mandatory attributes
            if self.myProperties[name]['mandatory']:
                raise AttributeError("Cannot remove mandatory attribute '%s'" % name)

            self.myProperties[name]['value'] = []
        else:
            raise AttributeError("no such property '%s'" % name)

    def _setattr_(self, name, value):
        """
        This is the setter method for object attributes.
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

        # A none value was passed to clear the value
        if value == None:
            self._delattr_(name)
            return

        # Try to save as property value
        if name in self.myProperties:

            # Check if this attribute is blocked by another attribute and its value.
            for bb in  self.myProperties[name]['blocked_by']:
                if bb['value'] in self.myProperties[bb['name']]['value']:
                    raise AttributeError("This attribute is blocked by %(name)s = '%(value)s'!" % bb)

            # Do not allow to write to read-only attributes.
            if self.myProperties[name]['readonly']:
                raise AttributeError("Cannot write to readonly attribute '%s'" % name)

            # Check if the given value has to match one out of a given list.
            if self.myProperties[name]['values'] != None and value not in self.myProperties[name]['values']:
                raise TypeError("Invalid value given for %s! Expected is one of %s" % (name,str(self.myProperties[name]['values'])))

            # Set the new value
            if self.myProperties[name]['multivalue']:

                # Check if the new value is s list.
                if type(value) != list:
                    raise TypeError("Invalid value given for %s, expected is a list for multi-value properties!" % (name,))
                new_value = value
            else:
                new_value = [value]

            # Eventually fixup value from incoming JSON string
            s_type = self.myProperties[name]['type']
            try:
                new_value = self._objectFactory.getAttributeTypes()[s_type].fixup(new_value)
            except Exception:
                raise TypeError("Invalid value given for %s (%s) expected is '%s'" % (name, new_value, s_type))

            # Check if the new value is valid
            #pylint: disable=E1101
            if not self._objectFactory.getAttributeTypes()[s_type].is_valid_value(new_value):
                raise TypeError("Invalid value given for %s (%s) expected is '%s'" % (name, new_value, s_type))

            # Validate value
            if self.myProperties[name]['validator']:
                res, error = self.__processValidator(self.myProperties[name]['validator'], name, new_value)
                if not res:
                    if len(error):
                        raise ValueError("Property (%s) validation failed! Last error was: %s" % (name, error[0]))
                    else:
                        raise ValueError("Property (%s) validation failed without error!" % (name,))

            # Ensure that unique values stay unique. Let the backend test this.
            #if self.myProperties[name]['unique']:
            #    backendI = ObjectBackendRegistry.getBackend(self.myProperties[name]['backend'])
            #    if not backendI.is_uniq(name, new_value):
            #        raise ObjectException("The property value '%s' for property %s is not unique!" % (value, name))

            # Assign the properties new value.
            self.myProperties[name]['value'] = new_value
            self.log.debug("updated property value of [%s|%s] %s:%s" % (type(self).__name__, self.uuid, name, new_value))

            # Update status if there's a change
            t = self.myProperties[name]['type']
            current = copy.deepcopy(self.myProperties[name]['value'])
            #pylint: disable=E1101
            if not self._objectFactory.getAttributeTypes()[t].values_match(self.myProperties[name]['value'], self.myProperties[name]['orig_value']):
                self.myProperties[name]['status'] = STATUS_CHANGED
                self.myProperties[name]['last_value'] = current

        else:
            raise AttributeError("no such property '%s'" % name)

    def _getattr_(self, name):
        """
        The getter method object attributes.

        (It differentiates between object attributes and class-members)
        """
        methods = getattr(self, '__methods')

        # If the requested property exists in the object-attributes, then return it.
        if name in self.myProperties:

            # We can have single and multivalues, return the correct type here.
            value = None
            if self.myProperties[name]['multivalue']:
                value = self.myProperties[name]['value']
                if not len(value) and self.myProperties[name]['default']:
                    value = self.myProperties[name]['default']
            else:
                if len(self.myProperties[name]['value']):
                    value = self.myProperties[name]['value'][0]
                elif self.myProperties[name]['default'] and len(self.myProperties[name]['default']):
                    value = self.myProperties[name]['default'][0]

            return(value)

        # The requested property-name seems to be a method, return the method reference.
        elif name in methods:
            return methods[name]['ref']

        else:
            raise AttributeError("no such property '%s'" % name)

    def getAttrType(self, name):
        """
        Return the type of a given object attribute.
        """

        if name in self.myProperties:
            return self.myProperties[name]['type']

        raise AttributeError("no such property '%s'" % name)

    def commit(self):
        """
        Commits changes of an object to the corresponding backends.
        """
        # Create a copy to avoid touching the original values
        props = copy.deepcopy(self.myProperties)

        # Check if _mode matches with the current object type
        #pylint: disable=E1101
        if self._base_object and not self._mode in ['create', 'remove', 'update']:
            raise ObjectException("mode '%s' not available for base objects" % self._mode)
        if not self._base_object and self._mode in ['create', 'remove']:
            raise ObjectException("mode '%s' only available for base objects" % self._mode)

        self.log.debug("saving object modifications for [%s|%s]" % (type(self).__name__, self.uuid))

        # Ensure that mandatory values are set, use default if possible
        for key in props:
            props[key]['commit_status'] = props[key]['status']
            if props[key]['mandatory'] and not len(props[key]['value']):
                if props[key]['default']:
                    props[key]['commit_status'] |= STATUS_CHANGED
                    props[key]['value'] = props[key]['default']
                    self.log.debug("used default for: %s <%s>" % (key, props[key]['value']))
                else:
                    raise ObjectException("The required property '%s' is not set!" % (key,))

        # Collect values by store and process the property filters
        toStore = {}
        collectedAttrs = {}
        for key in props:

            # Check if this attribute is blocked by another attribute and its value.
            is_blocked = False
            for bb in  props[key]['blocked_by']:
                if bb['value'] in props[bb['name']]['value']:
                    if props[key]['default']:
                        props[key]['value'] = copy.deepcopy(props[key]['default'])
                    else:
                        props[key]['value'] = props[key]['default']

                    is_blocked = True
                    break

            # Check if all required attributes are set. (Skip blocked once, they cannot be set!)
            if not is_blocked and props[key]['mandatory'] and not len(props[key]['value']):
                raise ObjectException("The required property '%s' is not set!" % (key,))

            # Adapt status from dependent properties.
            for propname in props[key]['depends_on']:
                props[key]['commit_status'] |= props[propname]['status'] & STATUS_CHANGED

            # Do not save untouched values
            if not props[key]['commit_status'] & STATUS_CHANGED:
                continue

            # Get the new value for the property and execute the out-filter
            self.log.debug("changed: %s" % (key,))

            # Process each and every out-filter with a clean set of input values,
            #  to avoid that return-values overwrite themselves.
            if len(props[key]['out_filter']):

                self.log.debug(" found %s out-filter for %s" % (str(len(props[key]['out_filter'])), key,))
                for out_f in props[key]['out_filter']:
                    self.__processFilter(out_f, key, props)

        # Collect properties by backend
        for prop_key in props:

            # Do not save untouched values
            if not props[prop_key]['commit_status'] & STATUS_CHANGED:
                continue

            collectedAttrs[prop_key] = props[prop_key]

        # Create a backend compatible list of all changed attributes.
        toStore = {}
        for prop_key in collectedAttrs:

            # Collect properties by backend
            for be in props[prop_key]['backend']:

                if not be in toStore:
                    toStore[be] = {}

                # Convert the properities type to the required format - if its not of the expected type.
                be_type = collectedAttrs[prop_key]['backend_type']
                s_type = collectedAttrs[prop_key]['type']
                if not self._objectFactory.getAttributeTypes()[be_type].is_valid_value(collectedAttrs[prop_key]['value']):
                    collectedAttrs[prop_key]['value'] = self._objectFactory.getAttributeTypes()[s_type].convert_to(
                            be_type, collectedAttrs[prop_key]['value'])

                # Append entry to the to-be-stored list
                toStore[be][prop_key] = {'foreign': collectedAttrs[prop_key]['foreign'],
                                    'orig': collectedAttrs[prop_key]['in_value'],
                                    'value': collectedAttrs[prop_key]['value'],
                                    'type': collectedAttrs[prop_key]['backend_type']}

        # Leave the show if there's nothing to do
        if not toStore:
            return

        # Update references using the toStore information
        changes = {}
        for be in toStore:
            changes.update(toStore[be])
        self.update_refs(changes)

        # Handle by backend
        p_backend = getattr(self, '_backend')
        obj = self

        zope.event.notify(ObjectChanged("pre %s" % self._mode, obj))

        # First, take care about the primary backend...
        if p_backend in toStore:
            be = ObjectBackendRegistry.getBackend(p_backend)
            if self._mode == "create":
                obj.uuid = be.create(self.dn, toStore[p_backend], self._backendAttrs[p_backend])

            elif self._mode == "extend":
                be.extend(self.uuid, toStore[p_backend],
                        self._backendAttrs[p_backend],
                        self.getForeignProperties())

            else:
                be.update(self.uuid, toStore[p_backend])

            # Eventually the DN has changed
            dn = be.uuid2dn(self.uuid)
            if dn != obj.dn:
                obj.dn = dn
                if self._base_object:
                    zope.event.notify(ObjectChanged("relocated", obj))
                obj.orig_dn = dn

        # ... then walk thru the remaining ones
        for backend, data in toStore.items():

            # Skip primary backend - already done
            if backend == p_backend:
                continue

            be = ObjectBackendRegistry.getBackend(backend)
            beAttrs = self._backendAttrs[backend] if backend in self._backendAttrs else {}
            if self._mode == "create":
                be.create(self.dn, data, beAttrs)
            elif self._mode == "extend":
                be.extend(self.uuid, data, beAttrs, self.getForeignProperties())
            else:
                be.update(self.uuid, data)

        zope.event.notify(ObjectChanged("post %s" % self._mode, obj))

    def revert(self):
        """
        Reverts all changes made to this object since it was loaded.
        """
        for key in self.myProperties:
            self.myProperties[key]['value'] = self.myProperties[key]['last_value']

        self.log.debug("reverted object modifications for [%s|%s]" % (type(self).__name__, self.uuid))

    def getExclusiveProperties(self):
        return [x for x, y in self.myProperties.items() if not y['foreign']]

    def getForeignProperties(self):
        return [x for x, y in self.myProperties.items() if y['foreign']]

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
        self.log.debug(" validator started (%s)" % (key))
        self.log.debug("  value: %s" % (value, ))

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
                fname = type(curline['condition']).__name__
                v = (curline['condition']).process(*args, **named)

                # Log what happend!
                self.log.debug("  %s: [Filter]  %s(%s) called and returned: %s" % (
                    lptr, fname, ", ".join(["\"" + x + "\"" for x in curline['params']]), v))

                # Append the result to the stack.
                stack.append(v)
                if not v:
                    if len(errors):
                        lasterrmsg =  errors.pop()

            # A comparator compares two values from the stack and then returns a single
            #  boolean value.
            elif 'operator' in curline:
                v1 = stack.pop()
                v2 = stack.pop()
                fname = type(curline['operator']).__name__
                res = (curline['operator']).process(v1, v2)
                stack.append(res)

                # Add last error message
                if not res:
                    errormsgs.append(lasterrmsg)
                    lasterrmsg = ""

                # Log what happend!
                self.log.debug("  %s: [OPERATOR]  %s(%s, %s) called and returned: %s" % (
                    lptr, fname, v1, v2, res))

        # Attach last error message
        res = stack.pop()
        if not res and lasterrmsg != "":
            errormsgs.append(lasterrmsg)

        self.log.debug(" <- VALIDATOR ENDED (%s)" % (key))
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

        # Log values
        self.log.debug(" -> FILTER STARTED (%s)" % (key))
        #for pkey in prop:
        #    self.log.debug("  %s: %s: %s" % (lptr, pkey, prop[pkey]['value']))

        # Process the list till we reach the end..
        while (lptr + 1) in fltr:

            # Get the current line and increase the process list pointer.
            lptr = lptr + 1
            curline = fltr[lptr]

            # A filter is used to manipulate the 'value' or the 'key' or maybe both.
            if 'filter' in curline:

                # Build up argument list
                args = [self, key, prop]
                fname = type(curline['filter']).__name__
                for entry in curline['params']:
                    args.append(entry)

                # Process filter and keep results
                try:
                    key, prop = (curline['filter']).process(*args)
                except Exception as e:
                    raise ObjectException("Failed to execute filter '%s' for attribute '%s': %s" % (fname, key, str(e)))

                # Ensure that the processed data is still valid.
                # Filter may mess things up and then the next cannot process correctly.
                if (key not in prop):
                    raise ObjectException("Filter '%s' returned invalid key property key '%s'!" % (fname, key))

                # Check if the filter returned all expected property values.
                for pk in prop:
                    if not all(k in prop[pk] for k in ('backend', 'value', 'type')):
                        missing = ", ".join(set(['backend', 'value', 'type']) - set(prop[pk].keys()))
                        raise ObjectException("Filter '%s' does not return all expected property values! '%s' missing." % (fname, missing))

                    # Check if the returned value-type is list or None.
                    if type(prop[pk]['value']) not in [list, type(None)]:
                        raise ObjectException("Filter '%s' does not return a 'list' as value for key %s (%s)!" % (
                            fname, pk, type(prop[pk]['value'])))

                self.log.debug("  %s: [Filter]  %s(%s) called " % (lptr, fname,
                    ", ".join(["\"" + x + "\"" for x in curline['params']])))

            # A condition matches for something and returns a boolean value.
            # We'll put this value on the stack for later use.
            elif 'condition' in curline:

                # Build up argument list
                args = [key] + curline['params']

                # Process condition and keep results
                stack.append((curline['condition']).process(*args))

                fname = type(curline['condition']).__name__
                self.log.debug("  %s: [Condition] %s(%s) called " % (lptr, fname, ", ".join(curline['params'])))

            # Handle jump, for example if a condition has failed, jump over its filter-chain.
            elif 'jump' in curline:

                # Jump to <line> -1 because we will increase the line ptr later.
                olptr = lptr
                if curline['jump'] == 'conditional':
                    if stack.pop():
                        lptr = curline['onTrue'] - 1
                    else:
                        lptr = curline['onFalse'] - 1
                else:
                    lptr = curline['to'] - 1

                self.log.debug("  %s: [Goto] %s ()" % (olptr, lptr))

            # A comparator compares two values from the stack and then returns a single
            #  boolean value.
            elif 'operator' in curline:
                a = stack.pop()
                b = stack.pop()
                stack.append((curline['operator']).process(a, b))

                fname = type(curline['operator']).__name__
                self.log.debug("  %s: [Condition] %s(%s, %s) called " % (lptr, fname, a, b))

            # Log current values
            #self.log.debug("  result")
            #for pkey in prop:
            #    self.log.debug("   %s: %s" % (pkey, prop[pkey]['value']))

        self.log.debug(" <- FILTER ENDED")
        return prop

    def __fillInPlaceholders(self, fltr):
        """
        This method fill in placeholder into in- and out-filters.
        """

        # Collect all property values
        propList = {}
        for key in self.myProperties:
            if self.myProperties[key]['multivalue']:
                propList[key] = self.myProperties[key]['value']
            else:
                if self.myProperties[key]['value'] and len(self.myProperties[key]['value']):
                    propList[key] = self.myProperties[key]['value'][0]
                else:
                    propList[key] = None

        # An inline function which replaces format string tokens
        def _placeHolder(x):
            try:
                x = x % propList
            except KeyError:
                pass

            return (x)

        # Walk trough each line of the process list an replace placeholders.
        for line in fltr:
            if 'params' in fltr[line]:
                fltr[line]['params'] = map(_placeHolder,
                        fltr[line]['params'])
        return fltr

    def get_references(self):
        res = []
        index = PluginRegistry.getInstance("ObjectIndex")

        for ref, info in self._objectFactory.getReferences(self.__class__.__name__).items():

            for ref_attribute, dsc in info.items():
                oval = self.myProperties[dsc[0][1]]['orig_value'][0]
                res.append((
                    ref_attribute,
                    dsc[0][1],
                    getattr(self, dsc[0][1]),
                    map(lambda s: s.decode('utf-8'),
                        index.xquery("collection('objects')/*/.[o:Type = '%s' and ./*/o:%s = '%s']/o:DN/string()" % (ref, ref_attribute, oval)))))

        return res

    def update_refs(self, data):
        for ref_attr, self_attr, value, refs in self.get_references():

            for ref in refs:

                # Next iterration if there's no change for the relevant
                # attribute
                if not self_attr in data:
                    continue

                # Load object and change value to the new one
                c_obj = ObjectProxy(ref)
                c_value = getattr(c_obj, ref_attr)

                if type(c_value) == list:
                    c_value = filter(lambda x: x != value, c_value)
                    c_value.append(data[self_attr]['value'][0])
                    setattr(c_obj, ref_attr, list(set(c_value)))

                else:
                    setattr(c_obj, ref_attr, data[self_attr]['value'][0])

                c_obj.commit()

    def remove_refs(self):
        for ref_attr, self_attr, value, refs in self.get_references():
            for ref in refs:
                c_obj = ObjectProxy(ref)
                c_value = getattr(c_obj, ref_attr)
                if type(c_value) == list:
                    c_value = filter(lambda x: x != value, c_value)
                    setattr(c_obj, ref_attr, c_value)

                else:
                    setattr(c_obj, ref_attr, None)

                c_obj.commit()


    def remove(self):
        """
        Removes this object - and eventually it's containements.
        """
        #pylint: disable=E1101
        if not self._base_object:
            raise ObjectException("cannot remove non base object - use retract")

        # Remove all references to ourselves
        self.remove_refs()

        # Collect backends
        backends = [getattr(self, '_backend')]

        # Collect all used backends
        for info in self.myProperties.values():
            for be in info['backend']:
                if not be in backends:
                   backends.append(be)

        # Remove for all backends, removing the primary one as the last one
        backends.reverse()
        obj = self
        zope.event.notify(ObjectChanged("pre remove", obj))

        for backend in backends:
            be = ObjectBackendRegistry.getBackend(backend)
            be.remove(obj.uuid)

        zope.event.notify(ObjectChanged("post remove", obj))

    def move(self, new_base):
        """
        Moves this object - and eventually it's containements.
        """
        #pylint: disable=E1101
        if not self._base_object:
            raise ObjectException("cannot move non base objects")

        # Collect backends
        backends = [getattr(self, '_backend')]

        # Collect all other backends
        for info in self.myProperties.values():
            for be in info['backend']:
                if not be in backends:
                   backends.append(be)

        obj = self
        zope.event.notify(ObjectChanged("pre move", obj))

        # Move for all backends (...)
        backends.reverse()
        for backend in backends:
            be = ObjectBackendRegistry.getBackend(backend)
            be.move(self.uuid, new_base)

        zope.event.notify(ObjectChanged("post move", obj))

    def retract(self):
        """
        Removes this object extension
        """
        #pylint: disable=E1101
        if self._base_object:
            raise ObjectException("base objects cannot be retracted")

        # Remove all references to ourselves
        self.remove_refs()

        # Collect backends
        backends = [getattr(self, '_backend')]
        be_attrs = {}

        for prop, info in self.myProperties.items():
            for backend in info['backend']:
                if not backend in backends:
                    backends.append(backend)

                if not backend in be_attrs:
                    be_attrs[backend] = []
                be_attrs[backend].append(prop)

        # Retract for all backends, removing the primary one as the last one
        backends.reverse()
        obj = self
        zope.event.notify(ObjectChanged("pre retract", obj))

        for backend in backends:
            be = ObjectBackendRegistry.getBackend(backend)
            r_attrs = self.getExclusiveProperties()

            # Remove all non exclusive properties
            remove_attrs = []
            for attr in be_attrs[backend]:
                if attr in r_attrs:
                    remove_attrs.append(attr)

            #TODO: retract: update refs if they're affected by
            #               remove_attrs

            #pylint: disable=E1101
            be.retract(self.uuid, [a for a in remove_attrs if self.is_attr_set(a)], self._backendAttrs[backend] \
                    if backend in self._backendAttrs else None)

        zope.event.notify(ObjectChanged("post retract", obj))

    def is_attr_set(self, name):
        return len(self.myProperties[name]['value'])

    def is_attr_using_default(self, name):
        return not self.is_attr_set(name) and self.myProperties[name]['default']


class IObjectChanged(Interface):

    def __init__(self, obj):
        pass


class IAttributeChanged(Interface):

    def __init__(self, attr, value):
        pass


class ObjectChanged(object):
    implements(IObjectChanged)

    def __init__(self, reason, obj):
        self.reason = reason
        self.uuid = obj.uuid
        self.dn = obj.dn
        self.orig_dn = obj.orig_dn


class AttributeChanged(object):
    implements(IAttributeChanged)

    def __init__(self, reason, obj, target):
        self.reason = reason
        self.target = target
        self.uuid = obj.uuid

from clacks.agent.objects.proxy import ObjectProxy
