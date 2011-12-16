# -*- coding: utf-8 -*-
import dbus.service
from gosa.common import Environment
from gosa.common.components import Plugin
from gosa.dbus import get_system_bus
import re
import sys
import traceback
import subprocess


class ServiceException(Exception):
    pass


class DBusUnixServiceHandler(dbus.service.Object, Plugin):

    __status_map = {'-': False, '+': True, '?': None}

    def __init__(self):
        conn = get_system_bus()
        dbus.service.Object.__init__(self, conn, '/com/gonicus/gosa/service')
        self.env = Environment.getInstance()
        self.svc_command = self.env.config.get("unix.service-command", default="/usr/sbin/service")

    def _validate(self, name, action=None):
        services = self.get_services()
        if not name in services:
            raise ServiceException("unknown service %s" % name)

        if action and not action in services[service]['actions']:
            raise ServiceException("action '%s' not supported for service %s" % (action, name))

    @dbus.service.method('com.gonicus.gosa', out_signature='i')
    def get_runlevel(self):
        #TODO
        # LC_ALL=C who -r
        # run-level 2  2011-12-06 15:01                   last=S
        return 5

    @dbus.service.method('com.gonicus.gosa', in_signature='i', out_signature='i')
    def set_runlevel(self, level):
        #TODO
        # init $level
        return 0

    @dbus.service.method('com.gonicus.gosa', in_signature='s', out_signature='b')
    def start(self, name):
        service = self._validate(name, "start")

        # Skip if running
        if service['running']:
            return True

        # Execute call
        return subprocess.call([self.svc_command, name, 'start']) == 0

    @dbus.service.method('com.gonicus.gosa', in_signature='s', out_signature='b')
    def stop(self, name):
        service = self._validate(name, "stop")

        # Skip if running
        if not service['running']:
            return True

        # Execute call
        return subprocess.call([self.svc_command, name, 'stop']) == 0

    @dbus.service.method('com.gonicus.gosa', in_signature='s', out_signature='b')
    def restart(self, name):
        service = self._validate(name, "restart")
        return subprocess.call([self.svc_command, name, 'restart']) == 0

    @dbus.service.method('com.gonicus.gosa', in_signature='s', out_signature='b')
    def reload(self, name):
        service = self._validate(name, "reload")

        # Skip if running
        if not service['running']:
            return False

        return subprocess.call([self.svc_command, name, 'reload']) == 0

    @dbus.service.method('com.gonicus.gosa', in_signature='s', out_signature='a{ss}')
    def get_service(self, name):
        services = self.get_services()
        if not name in services:
            raise NoSuchServiceException("unknown service %s" % name)

        return services[name]

    @dbus.service.method('com.gonicus.gosa', out_signature='e{se{ss}}')
    def get_services(self):

        #TODO: change this from the current implementation to:
        #      get_runlevel()
        #      for service in /etc/rc%level%.d/S* (not really, see "man run-parts" for more information)
        #          run "$svc_command $service" to find out about the usage
        #          if usage supports "status", run "$svc_command $service status" to find out if it's running
        #          if there is an icon for $service.(png|gif|jpeg), save the path

        services = {}
        state = re.compile(r"^\s*\[\s+([?+-])\s+\]\s+([^\s]+)\s*$")

        _svcs = subprocess.Popen([self.svc_command, '--status-all'],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE).communicate()
        svcs = (_svcs[0] + _svcs[1]).split('\n')

        for svc in svcs:
            try:
                status, service = state.match(svc).groups()
                services[service] = {
                        'running': self.__status_map[status],
                        'methods': ['start', 'stop', 'restart', 'reload'],
                        'icon': None}

            except AttributeError:
                pass

        return services
