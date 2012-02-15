# -*- coding: utf-8 -*-
import uuid
import datetime
from types import MethodType
from zope.interface import implements
from clacks.common.handler import IInterfaceHandler
from clacks.common import Environment
from clacks.common.utils import N_
from clacks.common.components import Command, PluginRegistry, ObjectRegistry, AMQPServiceProxy, Plugin
from sqlalchemy.sql import select, and_
from sqlalchemy import Table, Column, String, PickleType, DateTime, MetaData


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
        self.env= Environment.getInstance()
        obj = self.env.config.get("index.pool", default="objectpool")
        self.__engine = self.env.getDatabaseEngine('core')

        metadata = MetaData()

        self.__pool = Table(obj, metadata,
            Column('uuid', String(36), primary_key=True),
            Column('object', PickleType),
            Column('created', DateTime))

        metadata.create_all(self.__engine)

        # Establish the connection
        self.__conn = self.__engine.connect()

    def serve(self):
        sched= PluginRegistry.getInstance("SchedulerService").getScheduler()
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
            raise ValueError("reference %s not found" % ref)

        # Remove local object if needed
        if ref in self.__object:
            del self.__object[ref]

        self.__conn.execute(self.__pool.delete().where(self.__pool.c.uuid == ref))

    @Command(__help__=N_("Set property for object on stack"))
    def setObjectProperty(self, ref, name, value):
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
            raise ValueError("reference %s not found" % ref)

        if not name in objdsc['object']['properties']:
            raise ValueError("property %s not found" % name)

        if not self.__can_be_handled_locally(ref):
            proxy = self.__get_proxy(ref)
            return proxy.setObjectProperty(ref, name, value)

        return setattr(objdsc['object']['object'], name, value)

    @Command(__help__=N_("Get property from object on stack"))
    def getObjectProperty(self, ref, name):
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
            raise ValueError("reference %s not found" % ref)

        if not name in objdsc['object']['properties']:
            raise ValueError("property %s not found" % name)

        if not self.__can_be_handled_locally(ref):
            proxy = self.__get_proxy(ref)
            return proxy.getObjectProperty(ref, name)

        return getattr(objdsc['object']['object'], name)

    @Command(__help__=N_("Call method from object on stack"))
    def dispatchObjectMethod(self, ref, method, *args):
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
            raise ValueError("reference %s not found" % ref)

        if not method in objdsc['object']['methods']:
            raise ValueError("method %s not found" % method)

        if not self.__can_be_handled_locally(ref):
            proxy = self.__get_proxy(ref)
            return proxy.dispatchObjectMethod(ref, method, *args)

        return getattr(objdsc['object']['object'], method)(*args)

    @Command(__help__=N_("Instantiate object and place it on stack"))
    def openObject(self, oid, *args, **kwargs):
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
        if not self.__can_oid_be_handled_locally(oid):
            proxy = self.__get_proxy_by_oid(oid)
            return proxy.openObject(oid, *args)

        env = Environment.getInstance()

        # Use oid to find the object type
        obj_type = self.__get_object_type(oid)
        methods, properties = self.__inspect(obj_type)

        # Load instance, fill with dummy stuff
        ref = str(uuid.uuid1())

        # Make object instance and store it
        obj = obj_type(*args, **kwargs)

        # Add dynamic information - if available
        if hasattr(obj, 'get_attributes'):
            properties = properties + obj.get_attributes()
        if hasattr(obj, 'get_nmethods'):
            methods = properties + obj.get_methods()

        pickle = not hasattr(obj, "_no_pickle_")
        if not pickle:
            self.__object[ref] = obj

        objdsc = {'node': env.id,
                'oid': oid,
                'object': obj if pickle else None,
                'methods': methods,
                'properties': properties}

        self.__conn.execute(self.__pool.insert(), {
            'uuid': ref,
            'object': objdsc,
            'created': datetime.datetime.now(),
            })


        # Build property dict
        propvals = {}
        if properties:
            propvals = dict([(p, getattr(obj, p)) for p in properties])

        # Build result
        result = {"__jsonclass__":["json.JSONObjectFactory", [obj_type.__name__, ref, oid, methods, properties]]}
        result.update(propvals)
        print result

        return result

    def __get_object_type(self, oid):
        if not oid in ObjectRegistry.objects:
            raise ValueError("Unknown object OID %s" % oid)

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
            raise ValueError("Unknown object OID %s" % oid)
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
        tmp = self.__conn.execute(select([self.__pool.c.uuid, self.__pool.c.object, self.__pool.c.created], self.__pool.c.uuid == ref))
        res = tmp.fetchone()
        tmp.close()
        if not res:
            return None

        # Fill in local object if needed
        if ref in self.__object:
            res[1]['object'] = self.__object[ref]

        return {'uuid': res[0], 'object': res[1], 'created': res[2]}

    def __gc(self):
        self.env.log.debug("running garbage collector on object store")

        entries = self.__conn.execute(select([self.__pool.c.uuid],
            and_(self.__pool.c.created < datetime.datetime.now() -
                datetime.timedelta(hours=1), self.__pool.c.node ==
                self.env.id)))
        for entry in entries:
            ref = entry[0]
            #TODO: remove prints
            print "-----> do we have %s?" % ref
            if ref in self.__object:
                print "-----> YES!"
                del self.__object[ref]

        self.__conn.execute(self.__pool.delete().where(and_(self.__pool.c.created <
            datetime.datetime.now() - datetime.timedelta(hours=1),
            self.__pool.c.node == self.env.id)))
