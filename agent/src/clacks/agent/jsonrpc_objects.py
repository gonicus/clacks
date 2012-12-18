# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

import uuid
import datetime
from types import MethodType
from zope.interface import implements
from clacks.common.utils import N_
from clacks.common import Environment
from clacks.common.error import ClacksErrorHandler as C
from clacks.common.handler import IInterfaceHandler
from clacks.common.components import Command, PluginRegistry, ObjectRegistry, AMQPServiceProxy, Plugin


# Register the errors handled  by us
C.register_codes(dict(
    REFERENCE_NOT_FOUND=N_("Reference '%(ref)s' not found"),
    PROPERTY_NOT_FOUND=N_("Property '%(property)s' not found"),
    METHOD_NOT_FOUND=N_("Method '%(method)s' not found"),
    OBJECT_LOCKED=N_("Object '%(object)s' has been locked by '%(user)s' on %(when)s"),
    OID_NOT_FOUND=N_("Object OID '%(oid)s' not found"),
    NOT_OBJECT_OWNER=N_("Caller does not own the referenced object")
    ))


class JSONRPCObjectMapper(Plugin):
    """
    The *JSONRPCObjectMapper* is a clacks agent plugin that implements a stack
    which can handle object instances. These can be passed via JSONRPC using
    the *__jsonclass__* helper attribute and allows remote proxies to emulate
    the object on the stack. The stack can hold objects that have been
    retrieved by their *OID* using the :class:`clacks.common.components.objects.ObjectRegistry`.

    Example::

        >>> from clacks.common.components import AMQPServiceProxy
        >>> # Create connection to service
        >>> proxy = >>> AMQPServiceProxy('amqps://admin:secret@amqp.example.net/org.clacks')
        >>> pm = proxy.openObject('libinst.diskdefinition')
        >>> pm.getDisks()
        []
        >>> proxy.closeObject(str(pm))
        >>>

    This will indirectly use the object mapper on the agent side.
    """
    implements(IInterfaceHandler)
    _target_ = 'core'
    _priority_ = 70
    __proxy = {}
    __object = {}

    def __init__(self):
        self.env = Environment.getInstance()
        self.db = self.env.get_mongo_db('clacks')

    def serve(self):
        sched = PluginRegistry.getInstance("SchedulerService").getScheduler()
        sched.add_interval_job(self.__gc, minutes=10, tag='_internal', jobstore="ram")

    @Command(__help__=N_("List available object OIDs"))
    def listObjectOIDs(self):
        """
        Provide a list of domain wide available object OIDs.

        ``Return:`` list
        """
        cr = PluginRegistry.getInstance('CommandRegistry')
        return cr.objects.keys()

    @Command(__help__=N_("Close object and remove it from stack"))
    def closeObject(self, ref):
        """
        Close an object by its reference. This will free the object on
        the agent side.

        ================= ==========================
        Parameter         Description
        ================= ==========================
        ref               UUID / object reference
        ================= ==========================
        """
        if not self.__get_ref(ref):
            raise ValueError(C.make_error("REFERENCE_NOT_FOUND", ref=ref))

        # Remove local object if needed
        if ref in self.__object:
            del self.__object[ref]

        self.db.object_pool.remove({'uuid': ref})

    @Command(needsUser=True, __help__=N_("Set property for object on stack"))
    def setObjectProperty(self, user, ref, name, value):
        """
        Set a property on an existing stack object.

        ================= ==========================
        Parameter         Description
        ================= ==========================
        ref               UUID / object reference
        name              Property name
        value             Property value
        ================= ==========================
        """
        objdsc = self.__get_ref(ref)
        if not objdsc:
            raise ValueError(C.make_error("REFERENCE_NOT_FOUND", ref=ref))

        if not name in objdsc['object']['properties']:
            raise ValueError(C.make_error("PROPERTY_NOT_FOUND", property=name))

        if not self.__check_user(ref, user):
            raise ValueError(C.make_error("NO_OBJECT_OWNER"))

        if not self.__can_be_handled_locally(ref):
            proxy = self.__get_proxy(ref)
            return proxy.setObjectProperty(ref, name, value)

        return setattr(objdsc['object']['object'], name, value)

    @Command(needsUser=True, __help__=N_("Get property from object on stack"))
    def getObjectProperty(self, user, ref, name):
        """
        Get a property of an existing stack object.

        ================= ==========================
        Parameter         Description
        ================= ==========================
        ref               UUID / object reference
        name              Property name
        ================= ==========================

        ``Return``: mixed
        """
        objdsc = self.__get_ref(ref)
        if not objdsc:
            raise ValueError(C.make_error("REFERENCE_NOT_FOUND", ref=ref))

        if not name in objdsc['object']['properties']:
            raise ValueError(C.make_error("PROPERTY_NOT_FOUND", property=name))

        if not self.__check_user(ref, user):
            raise ValueError(C.make_error("NO_OBJECT_OWNER"))

        if not self.__can_be_handled_locally(ref):
            proxy = self.__get_proxy(ref)
            return proxy.getObjectProperty(ref, name)

        return getattr(objdsc['object']['object'], name)

    @Command(needsUser=True, __help__=N_("Call method from object on stack"))
    def dispatchObjectMethod(self, user, ref, method, *args):
        """
        Call a member method of the referenced object.

        ================= ==========================
        Parameter         Description
        ================= ==========================
        ref               UUID / object reference
        method            Method name
        args              Arguments to pass to the method
        ================= ==========================

        ``Return``: mixed
        """
        objdsc = self.__get_ref(ref)
        if not objdsc:
            raise ValueError(C.make_error("REFERENCE_NOT_FOUND", ref=ref))

        if not method in objdsc['object']['methods']:
            raise ValueError(C.make_error("METHOD_NOT_FOUND", method=method))

        if not self.__check_user(ref, user):
            raise ValueError(C.make_error("NO_OBJECT_OWNER"))

        #TODO: need to implement dispatchObjectMethodAsUser
        #if not self.__can_be_handled_locally(ref):
        #    proxy = self.__get_proxy(ref)
        #    return proxy.dispatchObjectMethodAsUser(user, ref, method, *args)

        return getattr(objdsc['object']['object'], method)(*args)

    @Command(needsUser=True, __help__=N_("Reloads the object"))
    def reloadObject(self, user, ref):
        """
        Opens a copy of the object given as ref and
        closes the original instance.
        """
        res = self.db.object_pool.find({'uuid': ref})
        if res.count():

            if not self.__check_user(ref, user):
                raise ValueError(C.make_error("NO_OBJECT_OWNER"))

            item = res[0]
            oid = item['object']['oid']
            uuid = item['object']['uuid']
            new_obj = self.openObject(user, oid, uuid)
            return new_obj
        else:
            raise ValueError(C.make_error("REFERENCE_NOT_FOUND", ref=ref))

    @Command(needsUser=True, __help__=N_("Removes the given object"))
    def removeObject(self, user, oid, *args, **kwargs):
        """
        Open object on the agent side and calls its remove method

        ================= ==========================
        Parameter         Description
        ================= ==========================
        oid               OID of the object to create
        args/kwargs       Arguments to be used when getting an object instance
        ================= ==========================

        ``Return``: True
        """

        #TODO: needs to implement removeObjectAsUser
        #if not self.__can_oid_be_handled_locally(oid):
        #    proxy = self.__get_proxy_by_oid(oid)
        #    return proxy.removeObjectAsUser(user, oid, *args)

        # In case of "object" we want to check the lock
        if oid == 'object':
            lck = self.db.object_pool.find_one({'$or': [
                {'object.uuid': args[0]},
                {'object.dn': args[0]}]},
                {'user': 1, 'created': 1})
            #TODO: re-enable locking
            #if lck:
            #    raise Exception(C.make_error("OBJECT_LOCKED", object=args[0],
            #        user=lck['user'],
            #        when=lck['created'].strftime("%Y-%m-%d (%H:%M:%S)")
            #        ))

        # Use oid to find the object type
        obj_type = self.__get_object_type(oid)

        # Make object instance and store it
        kwargs['user'] = user
        obj = obj_type(*args, **kwargs)
        obj.remove()
        return True

    @Command(needsUser=True, __help__=N_("Instantiate object and place it on stack"))
    def openObject(self, user, oid, *args, **kwargs):
        """
        Open object on the agent side. This creates an instance on the
        stack and returns an a JSON description of the object and it's
        values.

        ================= ==========================
        Parameter         Description
        ================= ==========================
        oid               OID of the object to create
        args/kwargs       Arguments to be used when getting an object instance
        ================= ==========================

        ``Return``: JSON encoded object description
        """

        #TODO: implement openObjectAsUser with proper ACL checks
        #if not self.__can_oid_be_handled_locally(oid):
        #    proxy = self.__get_proxy_by_oid(oid)
        #    return proxy.openObjectAsUser(user, oid, *args)

        # In case of "object" we want to check the lock
        if oid == 'object':
            lck = self.db.object_pool.find_one({'$or': [
                {'object.uuid': args[0]},
                {'object.dn': args[0]}]},
                {'user': 1, 'created': 1})
            #TODO: re-enable locking
            #if lck:
            #    raise Exception(C.make_error("OBJECT_LOCKED", object=args[0],
            #        user=lck['user'],
            #        when=lck['created'].strftime("%Y-%m-%d (%H:%M:%S)")
            #        ))

        env = Environment.getInstance()

        # Use oid to find the object type
        obj_type = self.__get_object_type(oid)
        methods, properties = self.__inspect(obj_type)

        # Load instance, fill with dummy stuff
        ref = str(uuid.uuid1())

        # Make object instance and store it
        kwargs['user'] = user
        obj = obj_type(*args, **kwargs)

        # Merge in methods that may be available later due to extending more addons
        methods += obj.get_all_method_names()

        # Add dynamic information - if available
        if hasattr(obj, 'get_attributes'):
            properties = properties + obj.get_attributes()
        if hasattr(obj, 'get_methods'):
            methods = methods + obj.get_methods()

        pickle = not hasattr(obj, "_no_pickle_")
        if not pickle:
            self.__object[ref] = obj

        objdsc = {'node': env.id,
                'oid': oid,
                'dn': obj.dn if hasattr(obj, 'dn') else None,
                'uuid': obj.uuid if hasattr(obj, 'uuid') else None,
                'object': obj if pickle else None,
                'methods': methods,
                'properties': properties}

        self.db.object_pool.save({
            'uuid': ref,
            'user': user,
            'node': self.env.id,
            'object': objdsc,
            'created': datetime.datetime.now()})

        # Build property dict
        propvals = {}
        if properties:
            propvals = dict([(p, getattr(obj, p)) for p in properties])

        propvals['uuid'] = obj.uuid

        # Build result
        result = {"__jsonclass__": ["json.JSONObjectFactory", [obj_type.__name__, ref, obj.dn, oid, methods, properties]]}
        result.update(propvals)

        return result

    def __check_user(self, ref, user):
        return self.db.object_pool.find_one({'uuid': ref, 'user': user}, {'user': 1}) != None

    def __get_object_type(self, oid):
        if not oid in ObjectRegistry.objects:
            raise ValueError(C.make_error("OID_NOT_FOUND", oid=oid))

        return ObjectRegistry.objects[oid]['object']

    def __inspect(self, clazz):
        methods = []
        properties = []

        for part in dir(clazz):
            if part.startswith("_"):
                continue
            obj = getattr(clazz, part)
            if isinstance(obj, MethodType):
                methods.append(part)
            if isinstance(obj, property):
                properties.append(part)

        return methods, properties

    def __can_be_handled_locally(self, ref):
        res = self.__get_ref(ref)
        return self.__can_oid_be_handled_locally(res['object']['oid'])

    def __can_oid_be_handled_locally(self, oid):
        if not oid in ObjectRegistry.objects:
            raise ValueError(C.make_error("OID_NOT_FOUND", oid=oid))
        return oid in ObjectRegistry.objects

    def __get_proxy(self, ref):
        res = self.__get_ref(ref)
        return self.__get_proxy_by_oid(res['object']['oid'])

    def __get_proxy_by_oid(self, oid):
        # Choose a possible node
        cr = PluginRegistry.getInstance('CommandRegistry')
        nodes = cr.get_load_sorted_nodes()
        provider = None

        # Get first match that is a provider for this object
        for provider in nodes.keys():
            if provider in cr.objects[oid]:
                break

        if not provider in self.__proxy:
            env = Environment.getInstance()
            queue = '%s.core.%s' % (env.domain, provider)
            amqp = PluginRegistry.getInstance("AMQPHandler")
            self.__proxy[provider] = AMQPServiceProxy(amqp.url['source'], queue)

        return self.__proxy[provider]

    def __get_ref(self, ref):
        res = self.db.object_pool.find_one({'uuid': ref})
        if not res:
            return None

        # Fill in local object if needed
        if ref in self.__object:
            res['object']['object'] = self.__object[ref]

        return res

    def __gc(self):
        self.env.log.debug("running garbage collector on object store")

        entries = self.db.object_pool.find({
            'created': {'$lt': datetime.datetime.now() - datetime.timedelta(hours=1)},
            'node': self.env.id}, {'uuid': 1})
        for entry in entries:
            ref = entry['uuid']
            if ref in self.__object:
                del self.__object[ref]

        self.db.object_pool.remove({
            'created': {'$lt': datetime.datetime.now() - datetime.timedelta(hours=1)},
            'node': self.env.id
            })
