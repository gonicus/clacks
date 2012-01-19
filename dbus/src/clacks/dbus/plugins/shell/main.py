import re
import os
import dbus.service
import logging
from subprocess import Popen, PIPE
from clacks.common import Environment
from clacks.common.components import Plugin
from clacks.dbus import get_system_bus
from json import loads


class DBusShellException(Exception):
    """
    Exception thrown for generic errors
    """
    pass


class NoSuchScriptException(DBusShellException):
    """
    Exception thrown for unknown scripts
    """
    pass


class DBusShellHandler(dbus.service.Object, Plugin):
    """
    The DBus shell handler exports shell scripts to the DBus.

    Scripts placed in '/etc/clacks/shell.d' can then be executed using the
    'shell_exec()' method.

    Exported scripts can be listed using the 'shell_list()' method.

    e.g.
        print proxy.clientDispatch("<clientUUID>", "dbus_shell_exec", "myScript.sh", [])

    (The 'dbus_' prefix in the above example was added by the clacks-client dbus-proxy
    plugin to mark exported dbus methods - See clacks-client proxy  plugin for details)
    """

    # The path were scripts were read from.
    script_path = None
    log = None

    def __init__(self):
        conn = get_system_bus()
        dbus.service.Object.__init__(self, conn, '/org/clacks/shell')
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.script_path = self.env.config.get("dbus.script_path", "/etc/clacks/shell.d").strip("'\"")
        self._reloadSignatures()

    def _reloadSignatures(self):
        """
        This method reads all scripts found in the 'dbus.script_path' and
        exports them as callable dbus-method.
        """

        # locate files in /etc/clacks/shell.d and find those matching
        self.scripts = {}
        path = self.script_path
        for f in [n for n in os.listdir(path) if re.match("^[a-zA-Z0-9][a-zA-Z0-9_\.]*$", n)]:
            data = self._parse_shell_script(os.path.join(path, f))
            self.scripts[data[0]] = data

    def _parse_shell_script(self, path):
        """
        This method executes the given script (path) with the parameter
        '--signature' to receive the scripts signatur.

        It returns a tuple containing all found agruments and their type.
        """

        # Call the script with the --signature parameter
        scall = Popen([path, '--signature'], stdout=PIPE, stderr=PIPE)
        scall.wait()

        # Check returncode of the script call.
        if scall.returncode != 0:
            self.log.debug("failed to read signature from D-Bus shell script '%s' (%s) " % (path, scall.stderr.read()))
            raise DBusShellException("failed to read signature from D-Bus shell script '%s' " % (path))

        # Check if we can read the returned signature.
        sig = {}
        try:
            sig = loads(scall.stdout.read())
        except ValueError:
            raise DBusShellException("failed to undertand signature of D-Bus shell script '%s'" % (path))

        # Signature was readable, now check if we got everything we need
        if not(('in' in sig and type(sig['in']) == list) or 'in' not in sig):
            raise DBusShellException("failed to undertand in-signature of D-Bus shell script '%s'" % (path))
        if 'out' not in sig or type(sig['out']) not in [str, unicode]:
            raise DBusShellException("failed to undertand out-signature of D-Bus shell script '%s'" % (path))

        return (os.path.basename(path), sig)

    @dbus.service.method('org.clacks', in_signature='', out_signature='a{s(ssssa(sss))}')
    def shell_list(self):
        """
        Returns all availabe scripts and their details.
        """
        return self.scripts

    @dbus.service.method('org.clacks', in_signature='sas', out_signature='a{sv}')
    def shell_exec(self, cmd, args):
        """
        Executes a shell command and returns the result with its return code
        stderr and stdout strings.
        """
        # Check if the given script exists
        if cmd not in self.scripts:
            raise NoSuchServiceException("unknown service %s" % cmd)

        # Execute the script and return the results
        args = map(lambda x: str(x), [os.path.join(self.script_path,cmd)] + args)
        res = Popen(args, stdout=PIPE, stderr=PIPE)
        res.wait()
        return ({'code': res.returncode,
                'stdout': res.stdout.read(),
                'stderr': res.stderr.read()})
