# -*- coding: utf-8 -*-
import copy
import re
import zope.event
import ldap
import ldap.dn
from logging import getLogger
from zope.interface import Interface, implements
from gosa.agent.objects.backend.registry import ObjectBackendRegistry

# Status
STATUS_OK = 0
STATUS_CHANGED = 1

_is_uuid = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')


class ObjectException(Exception):
    pass



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
    _mode = False
    _propsByBackend = {}
    uuid = None
    dn = None
    orig_dn = None
    log = None
    createTimestamp = None
    modifyTimestamp = None


    def __init__(self, where=None, mode="update"):

        # Instantiate Backend-Registry
        self._reg = ObjectBackendRegistry.getInstance()
        self.log = getLogger(__name__)
        self.log.debug("new object instantiated '%s'" % (type(self).__name__))

        # Group attributes by Backend
        propsByBackend = {}
        props = getattr(self, '__properties')
        for key in props:

            # Initialize an empty array for each backend
            for be in props[key]['backend']:
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

        # Use default value for newly created objects.
        for key in props:
            if not(props[key]['value']) and props[key]['default'] != None:
                props[key]['value'] = copy.deepcopy(props[key]['default'])

                # Only set status to modified for values with a valid default.
                if len(props[key]['default']):
                    props[key]['status'] = STATUS_CHANGED

    def listProperties(self):
        props = getattr(self, '__properties')
        return(props.keys())

    def listMethods(self):
        methods = getattr(self, '__methods')
        return(methods.keys())

    def hasattr(self, attr):
        props = getattr(self, '__properties')
        return attr in props

    def _read(self, where):
        """
        This method tries to initialize a GOsa-object instance by reading data
        from the defined backend.

        Attributes will be grouped by their backend to ensure that only one
        request per backend will be performed.

        """
        props = getattr(self, '__properties')

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
                info = dict([(k, props[k]['backend_type']) for k in self._propsByBackend[backend]])
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
                props[key]['in_value'] = props[key]['value'] = attrs[key]
                self.log.debug("%s: %s" % (key, props[key]['value']))

        # Once we've loaded all properties from the backend, execute the
        # in-filters.
        for key in props:

            # Skip loading in-filters for None values
            if props[key]['value'] == None:
                props[key]['in_value'] = props[key]['value'] = []
                continue

            # Execute defined in-filters.
            if len(props[key]['in_filter']):
                self.log.debug("found %s in-filter(s)  for attribute '%s'" % (str(len(props[key]['in_filter'])),key))

                # Execute each in-filter
                for in_f in props[key]['in_filter']:
                    self.__processFilter(in_f, key, props)

        # Convert the received type into the target type if not done already
        #pylint: disable=E1101
        atypes = self._objectFactory.getAttributeTypes()
        for key in props:

            # Convert values from incoming backend-type to required type
            if props[key]['value']:
                a_type = props[key]['type']
                be_type = props[key]['backend_type']

                #  Convert all values to required type
                if not atypes[a_type].is_valid_value(props[key]['value']):
                    try:
                        props[key]['value'] = atypes[a_type].convert_from(be_type, props[key]['value'])
                    except Exception as e:
                        self.log.error("conversion of '%s' from '%s' to type '%s' failed: %s", (key, be_type, a_type, str(e)))
                    else:
                        self.log.debug("converted '%s' from type '%s' to type '%s'!" % (key, be_type, a_type))

            # Keep the initial value
            props[key]['last_value'] = props[key]['orig_value'] = copy.deepcopy(props[key]['value'])

    def _delattr_(self, name):
        """
        Deleter method for properties.
        """
        props = getattr(self, '__properties')
        if name in props:

            # Check if this attribute is blocked by another attribute and its value.
            for bb in  props[name]['blocked_by']:
                if bb['value'] in props[bb['name']]['value']:
                    raise AttributeError("This attribute is blocked by %(name)s = '%(value)s'!" % bb)

            # Do not allow to write to read-only attributes.
            if props[name]['readonly']:
                raise AttributeError("Cannot write to readonly attribute '%s'" % name)

            # Do not allow remove mandatory attributes
            if props[name]['mandatory']:
                raise AttributeError("Cannot remove mandatory attribute '%s'" % name)

            props[name]['value'] = []
        else:
            raise AttributeError("no such property '%s'" % name)

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

        # A none value was passed to clear the value
        if value == None:
            self._delattr_(name)
            return

        # Try to save as property value
        props = getattr(self, '__properties')
        if name in props:

            # Check if this attribute is blocked by another attribute and its value.
            for bb in  props[name]['blocked_by']:
                if bb['value'] in props[bb['name']]['value']:
                    raise AttributeError("This attribute is blocked by %(name)s = '%(value)s'!" % bb)

            # Do not allow to write to read-only attributes.
            if props[name]['readonly']:
                raise AttributeError("Cannot write to readonly attribute '%s'" % name)

            # Check if the given value has to match one out of a given list.
            if props[name]['values'] != None and value not in props[name]['values']:
                raise TypeError("Invalid value given for %s! Expected is one of %s" % (name,str(props[name]['values'])))

            # Set the new value
            if props[name]['multivalue']:

                # Check if the new value is s list.
                if type(value) != list:
                    raise TypeError("Invalid value given for %s, expected is a list for multi-value properties!" % (name,))
                new_value = value
            else:
                new_value = [value]

            # Check if the new value is valid
            s_type = props[name]['type']
            #pylint: disable=E1101
            if not self._objectFactory.getAttributeTypes()[s_type].is_valid_value(new_value):
                raise TypeError("Invalid value given for %s" % (name,))


            # Validate value
            if props[name]['validator']:
                res, error = self.__processValidator(props[name]['validator'], name, new_value)
                if not res:
                    if len(error):
                        raise ValueError("Property (%s) validation failed! Last error was: %s" % (name, error[0]))
                    else:
                        raise ValueError("Property (%s) validation failed without error!" % (name,))

            # Ensure that unique values stay unique. Let the backend test this.
            #if props[name]['unique']:
            #    backendI = ObjectBackendRegistry.getBackend(props[name]['backend'])
            #    if not backendI.is_uniq(name, new_value):
            #        raise ObjectException("The property value '%s' for property %s is not unique!" % (value, name))

            # Assign the properties new value.
            props[name]['value'] = new_value
            self.log.debug("updated property value of [%s|%s] %s:%s" % (type(self).__name__, self.uuid, name, new_value))

            # Update status if there's a change
            t = props[name]['type']
            current = copy.deepcopy(props[name]['value'])
            #pylint: disable=E1101
            if not self._objectFactory.getAttributeTypes()[t].values_match(props[name]['value'], props[name]['orig_value']):
                props[name]['status'] = STATUS_CHANGED
                props[name]['last_value'] = current

        else:
            raise AttributeError("no such property '%s'" % name)

    def _getattr_(self, name):
        """
        The getter method GOsa-object attributes.

        (It differentiates between GOsa-object attributes and class-members)
        """
        props = getattr(self, '__properties')
        methods = getattr(self, '__methods')

        # If the requested property exists in the object-attributes, then return it.
        if name in props:

            # We can have single and multivalues, return the correct type here.
            if props[name]['multivalue']:
                value = props[name]['value']
            else:
                if len(props[name]['value']):
                    value = props[name]['value'][0]
                else:
                    value = None

            return(value)

        # The requested property-name seems to be a method, return the method reference.
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
        # Create a copy to avoid touching the original values
        props = copy.deepcopy(getattr(self, '__properties'))

        # Check if _mode matches with the current object type
        #pylint: disable=E1101
        if self._base_object and not self._mode in ['create', 'remove', 'update']:
            raise ObjectException("mode '%s' not available for base objects" % self._mode)
        if not self._base_object and self._mode in ['create', 'remove']:
            raise ObjectException("mode '%s' only available for base objects" % self._mode)

        self.log.debug("saving object modifications for [%s|%s]" % (type(self).__name__, self.uuid))

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
            props[key]['commit_status'] = props[key]['status']
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

        from pprint import pprint
        pprint(toStore)

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

                #TODO: update - check for changed attrs, if they affect something,
                #      let all backends remove the refs.

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
                #TODO: update - check for changed attrs, if they affect something,
                #      let all backends remove the refs.
                be.update(self.uuid, data)

        zope.event.notify(ObjectChanged("post %s" % self._mode, obj))

    def revert(self):
        """
        Reverts all changes made to this object since it was loaded.
        """
        props = getattr(self, '__properties')
        for key in props:
            props[key]['value'] = props[key]['last_value']

        self.log.debug("reverted object modifications for [%s|%s]" % (type(self).__name__, self.uuid))

    def getExclusiveProperties(self):
        props = getattr(self, '__properties')
        return [x for x, y in props.items() if not y['foreign']]

    def getForeignProperties(self):
        props = getattr(self, '__properties')
        return [x for x, y in props.items() if y['foreign']]

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
        props = getattr(self, '__properties')
        for key in props:
            if props[key]['multivalue']:
                propList[key] = props[key]['value']
            else:
                if props[key]['value'] and len(props[key]['value']):
                    propList[key] = props[key]['value'][0]
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

    def remove(self):
        """
        Removes this object - and eventually it's containements.
        """
        #pylint: disable=E1101
        if not self._base_object:
            raise ObjectException("cannot remove non base object - use retract")

        props = getattr(self, '__properties')

        # Collect backends
        backends = [getattr(self, '_backend')]

        # Collect all used backends
        for info in props.values():
            for be in info['backend']:
                if not be in backends:
                   backends.append(be)

        # Remove for all backends, removing the primary one as the last one
        backends.reverse()
        obj = self
        zope.event.notify(ObjectChanged("pre remove", obj))

        #TODO: update - check for remove_attrs, if they affect something,
        #      let all backends remove the refs.

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

        props = getattr(self, '__properties')

        # Collect backends
        backends = [getattr(self, '_backend')]

        # Collect all other backends
        for info in props.values():
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

        # Check if the move interacts with other objects
        #TODO

        zope.event.notify(ObjectChanged("post move", obj))

    def retract(self):
        """
        Removes this object extension
        """
        #pylint: disable=E1101
        if self._base_object:
            raise ObjectException("base objects cannot be retracted")

        props = getattr(self, '__properties')

        # Collect backends
        backends = [getattr(self, '_backend')]
        be_attrs = {}

        for prop, info in props.items():
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

            # Check if the move interacts with other objects
            #TODO: update - check for remove_attrs, if they affect something,
            #      let all backends remove the refs.

            #pylint: disable=E1101
            be.retract(self.uuid, [a for a in remove_attrs if getattr(obj, a)], self._backendAttrs[backend] if backend in self._backendAttrs else None)

        zope.event.notify(ObjectChanged("post retract", obj))


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
