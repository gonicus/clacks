# -*- coding: utf-8 -*-
import re
import select
import platform
import shlex
import subprocess
from threading import Thread
from Queue import Queue


if platform.system() != "Windows":
    from clacks.common.components.dbus_runner import DBusRunner
    import dbus
    import avahi
else:
    #pylint: disable=F0401
    import pybonjour


class ZeroconfException(Exception):
    pass


class ZeroconfClient(object):
    """
    The ZeroconfClient class helps with browsing for announced services. It
    creates a separate thread and needs the registrated service to look for
    as a parameter.

    Usage example::

        >>> import time
        >>> import ZerconfClient
        >>>
        >>> # This is the function called on changes
        >>> def callback(sdRef, flags, interfaceIndex, errorCode, fullname,
        ...                         hosttarget, port, txtRecord):
        ...   print('Resolved service:')
        ...   print('  fullname   =', fullname)
        ...   print('  hosttarget =', hosttarget)
        ...   print('  TXT        =', txtRecord)
        ...   print('  port       =', port)
        >>>
        >>> # Get instance and tell client to start
        >>> z= ZeroconfClient(['_amqps._tcp'], callback=callback)
        >>> z.start()
        >>>
        >>> # Do some sleep until someone presses Ctrl+C
        >>> try:
        >>>     while True:
        >>>         time.sleep(1)
        >>> except KeyboardInterrupt:
        >>>     # Shutdown client
        >>>     z.stop()
        >>>     exit()

    =============== ============
    Parameter       Description
    =============== ============
    regtypes        The service list to watch out for - i.e. _amqps._tcp
    timeout         The timeout in seconds
    callback        Method to call when we've received something
    domain          optional DNS domain to discover
    direct          Do not use python DBUS, but the avahi-browse binary
    =============== ============
    """
    __resolved = []
    __services = {}
    oneshot = False

    def __init__(self, regtypes, timeout=2.0, callback=None, domain='local',
            direct=False):
        self.__timeout = timeout
        self.__callback = callback
        self.__regtypes = regtypes
        self.__domain = domain
        self.__server = None
        self.__thread = None
        self.__runner = None
        self.active = False

        if platform.system() != "Windows":
            if direct:
                self.start = self.startDirect
                self.stop = self.stopDirect
            else:
                self.start = self.startAvahi
                self.stop = self.stopAvahi
        else:
            self.start = self.startPybonjour
            self.stop = self.stopPybonjour

    def __get_path(self, txt):
        l = avahi.txt_array_to_string_array(txt)

        for k in l:
            if k[:5] == "path=":
                if k[5:].startswith("/"):
                    return k[5:]
                else:
                    return "/" + k[5:]

        return "/"

    def __get_service(self, txt):
        l = avahi.txt_array_to_string_array(txt)

        for k in l:
            if k[:8] == "service=":
                return k[8:]

        return None

    @staticmethod
    def discover(regs, domain=None, direct=False):
        q = Queue()

        def done_callback(services):
            q.put(services)

        mdns = ZeroconfClient(regs, callback=done_callback, direct=direct)
        mdns.start()

        if domain:
            sddns = ZeroconfClient(regs, callback=done_callback, domain=domain,
                    direct=direct)
            sddns.start()

        while True:
            urls = q.get()
            q.task_done()
            if urls:
                break

        if domain:
            sddns.stop()
        mdns.stop()

        return urls

    def startDirect(self):
        self.active = True

        def runner():
            services = None

            while self.active:
                # Find local services
                services = self.__direct_start("avahi-browse -atkpr")

                # If there are none, check global services
                if not services:
                    services = self.__direct_start("avahi-browse -atkpr -d %s" % self.domain)

                self.__callback([] if not services else services)

        self.__thread = Thread(target=runner)
        self.__thread.start()

    def __direct_start(self, cmd):
        service = []
        args = shlex.split(cmd)
        output, error = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if error:
            return []

        for line in output.split('\n'):
            if line.startswith("="):
                flag, device, wproto, dsc, proto, loc, address, ip, port, txt = line.split(";") #@UnusedVariable
                txt = re.findall(r'"([^"]+)"', txt)
                if txt:
                    info = dict([v.split("=")[0:2] for v in txt])
                    if 'service' in info and info['service'] == 'clacks':
                        service.append("%s://%s:%s%s" % (proto.split(".")[0][1:], address, port, info['path'] if info['path'].startswith("/") else "/" + info["path"]))

        return list(set(service))

    def stopDirect(self):
        self.active = False
        self.__thread.join()

    def startAvahi(self):
        self.__runner = DBusRunner.get_instance()
        bus = self.__runner.get_system_bus()
        bus.add_signal_receiver(self.__dbus_connect, "NameOwnerChanged", "org.freedesktop.DBus", arg0="org.freedesktop.Avahi")
        self.__avahi_start()

    def __avahi_start(self):
        bus = self.__runner.get_system_bus()
        self.__server = dbus.Interface(
            bus.get_object(avahi.DBUS_NAME, avahi.DBUS_PATH_SERVER),
            avahi.DBUS_INTERFACE_SERVER)

        # Register for all types we're interested in
        for reg_type in self.__regtypes:
            self.__registerServiceTypeAvahi(reg_type)

        self.__runner.start()

    def stopAvahi(self):
        self.__runner.stop()

    def __dbus_connect(self, a, connect, disconnect):
        if connect != "":
            self.stopAvahi()
        else:
            self.__avahi_start()

    def __registerServiceTypeAvahi(self, reg_type):
        bus = self.__runner.get_system_bus()
        sbrowser = dbus.Interface(
                        bus.get_object(
                            avahi.DBUS_NAME,
                            self.__server.ServiceBrowserNew(
                                avahi.IF_UNSPEC,
                                avahi.PROTO_INET,
                                reg_type,
                                self.__domain,
                                dbus.UInt32(0))),
                       avahi.DBUS_INTERFACE_SERVICE_BROWSER)

        sbrowser.connect_to_signal("ItemNew", self.__newServiceAvahi)
        sbrowser.connect_to_signal("ItemRemove", self.__removeServiceAvahi)
        #sbrowser.connect_to_signal("AllForNow", self.__allForNowAvahi)
        #sbrowser.connect_to_signal("Failure", self.__errorCallbackAvahi)

    #pylint: disable=W0613
    def __newServiceAvahi(self, interface, protocol, name, stype, domain, flags):
        #pylint: disable=W0612
        self.__server.ResolveService(interface, protocol, name, stype, domain, avahi.PROTO_INET, dbus.UInt32(0), reply_handler=self.__service_resolved, error_handler=self.__print_error)

    def __print_error(self, err):
        try:
            from clacks.common import Environment
            env = Environment.getInstance()
            env.log.error(err)
        except:
            pass

    def __service_resolved(self, interface, protocol, name, stype, domain, host, aprotocol, address, port, txt, flags):
        # Conversation to URL
        if port == 80:
            port = ''
        else:
            port = ':%i' % port

        if self.__get_service(txt) == "clacks":
            path = self.__get_path(txt)
            url = "%s://%s%s%s" % (stype[1:].split(".")[0], host, port, path)
            self.__services[(interface, protocol, name, stype, domain)] = url.encode('ascii')

        self.__callback(self.__services.values())

    def __removeServiceAvahi(self, interface, protocol, name, stype, domain):
        del self.__services[(interface, protocol, name, stype, domain)]

    def __allForNowAvahi(self):
        self.__callback(self.__services.values())

    def __errorCallbackAvahi(self, *args):
        raise ZeroconfException("DBUS communication error: %s" % str(args[0]))

    def startPybonjour(self):
        self.active = True
        browse_sdRefs = []

        # Start the bonjour event processing.
        for reg_type in self.__regtypes: #@UnusedVariable
            browse_sdRefs.append(pybonjour.DNSServiceBrowse(regtype=self.__regtypes,
                callBack=self.__browseCallback))

        def runner():
            try:
                browse_sdRef = None
                while self.active:
                    ready = select.select(browse_sdRefs, [], [],
                        self.__timeout)

                    for browse_sdRef in browse_sdRefs:
                        if browse_sdRef in ready[0]:
                            pybonjour.DNSServiceProcessResult(browse_sdRef)
            finally:
                if browse_sdRef:
                    browse_sdRef.close()

        self.__thread = Thread(target=runner)
        self.__thread.start()

    def stopPybonjour(self):
        self.active = False
        self.__thread.join()

    def __resolveCallback(self, sdRef, flags, interfaceIndex, errorCode,
                        fullname, host, port, txt):
        if errorCode == pybonjour.kDNSServiceErr_NoError:

            # Conversation to URL
            if port == 80:
                port = ''
            else:
                port = ':%i' % port

            if self.__get_service(txt) == "clacks":
                path = self.__get_path(txt)
                url = "%s://%s%s%s" % (fullname.split(".")[-4:-3][0][1:], host, port, path)
                self.__callback([url.encode('ascii')])

            self.__resolved.append(True)

    def __browseCallback(self, sdRef, flags, interfaceIndex, errorCode,
                    serviceName, regtype, replyDomain):
        if errorCode != pybonjour.kDNSServiceErr_NoError:
            return

        # Service removed
        if not (flags & pybonjour.kDNSServiceFlagsAdd):
            return

        # Service added
        resolve_sdRef = pybonjour.DNSServiceResolve(0,
            interfaceIndex,
            serviceName,
            regtype,
            replyDomain,
            self.__resolveCallback)

        try:
            while not self.__resolved:
                ready = select.select([resolve_sdRef], [], [], self.__timeout)
                if resolve_sdRef not in ready[0]:
                    pass
                pybonjour.DNSServiceProcessResult(resolve_sdRef)
            else:
                self.__resolved.pop()
        finally:
            resolve_sdRef.close()
