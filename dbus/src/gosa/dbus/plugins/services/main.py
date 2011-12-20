# -*- coding: utf-8 -*-
import dbus.service
from os.path import basename
from gosa.common import Environment
from gosa.common.components import Plugin
from gosa.dbus import get_system_bus
from json import dumps, loads
import re
import sys
import traceback
import subprocess


class ServiceException(Exception):
    pass

class NoSuchServiceException(ServiceException):
    pass

class DBusUnixServiceHandler(dbus.service.Object, Plugin):

    __status_map = {'-': False, '+': True, '?': None}

    def __init__(self):
        conn = get_system_bus()
        dbus.service.Object.__init__(self, conn, '/com/gonicus/gosa/service')
        self.env = Environment.getInstance()
        self.svc_command = self.env.config.get("unix.service-command", default="/usr/sbin/service")

    def _validate(self, name, action=None):
        services = loads(str(self.get_services()))
        if not name in services:
            raise ServiceException("unknown service %s" % name)

        if action and not action in services[name]['actions']:
            raise ServiceException("action '%s' not supported for service %s" % (action, name))

        return services[name]

    @dbus.service.method('com.gonicus.gosa', out_signature='i')
    def get_runlevel(self):
        """
        Returns the current runlevel of the clacks-client.
        """

        # Call 'who -r' and parse the return value to get the run-level
        # run-level 2  Dec 19 01:21                   last=S
        process = subprocess.Popen(["who","-r"], env={'LC_ALL': 'C'}, \
                shell=False, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
        ret = process.communicate()
        rl = re.sub("^run-level[ ]*([0-9]*).*$","\\1", ret[0].strip())
        return int(rl)

    @dbus.service.method('com.gonicus.gosa', in_signature='i', out_signature='i')
    def set_runlevel(self, level):
        """
        Sets a new runlevel for the clacks-client
        """
        process = subprocess.Popen(["telinit","%s" % (str(level))], shell=False, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
        ret = process.communicate()
        return process.returncode

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

    #@dbus.service.method('com.gonicus.gosa', in_signature='s', out_signature='a{ss}')
    @dbus.service.method('com.gonicus.gosa', in_signature='s', out_signature='s')
    def get_service(self, name):
        services = loads(str(self.get_services()))
        if not name in services:
            raise NoSuchServiceException("unknown service %s" % name)

        return dumps(services[name])

    @dbus.service.method('com.gonicus.gosa', out_signature='s')
    def get_services(self):

        # Get the current runlevel and then check for registered services using
        #  run-parts --test --regex=^S* /etc/rc<level>.d
        level = self.get_runlevel()
        process = subprocess.Popen(["run-parts", "--test", "--regex=^S*", "/etc/rc%s.d" % (str(level))],
                shell=False, stdout=subprocess.PIPE,  stderr=subprocess.PIPE, env={'LC_ALL': 'C'})
        ret = process.communicate()

        # Parse results and strip out path infos and S[0-9] prefix
        services = {}
        for entry in ret[0].split("\n"):
            sname = re.sub("^S[0-9]*", "", basename(entry))

            # Do not add empty service names
            if not sname:
                continue

            # Try to detect the service actions we can perform (e.g. start/stop)
            _svcs = subprocess.Popen([self.svc_command, sname], env={'LC_ALL': 'C'},
                    stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
            content = _svcs[0] + _svcs[1]

            # Search useable service actions in the result
            res = re.findall("(([a-zA-Z\-]*)\|)", content, re.MULTILINE) + re.findall("(\|([a-zA-Z\-]*))", content, re.MULTILINE)
            l = set()
            for entry in res:
                l |= set([entry[1]],)

            # Create a service entry for the result
            services[sname] = {'actions': list(l), 'running': None, 'icon': None}

            # Check if the service running by calling 'status', if available
            if 'status' in services[sname]['actions']:
                _svcs = subprocess.Popen([self.svc_command, sname, 'status'], env={'LC_ALL': 'C'},
                        stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

                # Search for a string which tells us that the service is running
                # Be careful some infos return values like this:
                #  * isn't running | is not running | not running | failed (running) ...
                services[sname]['running'] = re.search('is running', _svcs[0]+_svcs[1], flags=re.IGNORECASE) != None

        return dumps(services)
