"""

Clacks D-Bus Shell plugin
^^^^^^^^^^^^^^^^^^^^^^^^^


The clacks-dbus shell plugin allows to execute shell scripts
on the client side with root privileges.

Scripts can be executed like this:

>>> clacksh
>>>  Suche Dienstanbieter...
>>> ...
>>> clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "dbus_shell_list")
>>> [u'script1.sh', u'test.py']

>>> clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "dbus_shell_exec", "script1.sh", ['param1', 'param2'])
>>> {u'code': 0, u'stderr': u'', u'stdout': u'result'}


Creating scripts
^^^^^^^^^^^^^^^^

Create a new executable file in ``/etc/clacks/shell.d`` and ensure that its name match the
following expression ``^[a-zA-Z0-9][a-zA-Z0-9_\.]*$``.

The script can contain any programming language you want, it just has to be executable
and has to act on the parameter '-- --signature', see below.


The parameter -- --signature
.........................

Each script has to return a signature when it is used with the parameter '-- --signature'.
This is required to populate the method to the clacks-dbus process.

A signature is a json string describing what is required and what is returned by the
script. See `dbus-python tutorial from freedesktop.org <http://dbus.freedesktop.org/doc/dbus-python/doc/tutorial.html>`_
for details on signatures.

Usually you'll pass strings to the script and it will return a string again:

>>> {"in": [{"param1": "s"},{"param2": "s"}], "out": "s"}


Example script
..............

Here is an example script:

>>>   #!/bin/bash
>>>   detail="-1"
>>>   dir=$HOME
>>>
>>>   usage() {
>>>       echo $(basename $0) [--detail] [--directory DIR]
>>>       exit 0
>>>   }
>>>
>>>   set -- `getopt -n$0 -u -a --longoptions="signature detail directory:" "h" "$@"` || usage
>>>   [ $# -eq 0 ] && usage
>>>
>>>   while [ $# -gt 0 ]
>>>   do
>>>       case "$1" in
>>>          --signature)
>>>              echo '{"in": [{"detail": "b"},{"directory": "s"}], "out": "s"}'
>>>              exit 0
>>>              ;;
>>>          --detail)
>>>              detail="-la"
>>>              ;;
>>>          --directory)
>>>              dir=$2
>>>              shift
>>>              ;;
>>>          -h)        usage;;
>>>          --)        shift;break;;
>>>          -*)        usage;;
>>>          *)         break;;
>>>       esac
>>>       shift
>>>   done
>>> ls $detail $dir

"""

import re
import os
import dbus.service
import logging
import inspect
from clacks.dbus.plugins.shell.shelldnotifier import ShellDNotifier
from subprocess import Popen, PIPE
from clacks.common import Environment
from clacks.common.components import Plugin
from clacks.dbus import get_system_bus
from json import loads
from dbus import validate_interface_name, Signature


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
    file_regex = "^[a-zA-Z0-9][a-zA-Z0-9_\.]*$"
    conn = None

    def __init__(self):
        self.scripts = {}

        # Connect to D-Bus service
        conn = get_system_bus()
        self.conn = conn
        dbus.service.Object.__init__(self, conn, '/org/clacks/shell')

        # Initialize paths and logging
        self.log = logging.getLogger(__name__)
        self.env = Environment.getInstance()
        self.script_path = self.env.config.get("dbus.script_path", "/etc/clacks/shell.d").strip("'\"")

        # Start notifier for file changes in /etc/clacks/shell.d
        ShellDNotifier(self.script_path, self.file_regex, self.__notifier_callback)

        # Intitially load all signatures
        self.__notifier_callback()

    @dbus.service.signal('org.clacks', signature='s')
    def _signatureChanged(self, filename):
        """
        Sends a signal on the dbus named '_signatureChanged' this can then be received
        by other processes like the clacks-client.
        """
        pass

    def __notifier_callback(self, filename = None):
        """
        This method reads scripts found in the 'dbus.script_path' and
        exports them as callable dbus-method.
        """

        # Check if we've the required permissions to access the shell.d directory
        if os.path.exists(self.script_path):

            # If the 'filename' was None then reload all scripts else reload the
            # script given by 'filename'
            if filename == None:
                self.scripts = {}
                path = self.script_path
                for filename in [n for n in os.listdir(path)]:
                    self._reload_signature(filename)
            else:

                # Get the script path and try to load the signatures
                self._reload_signature(filename)

            self.log.info("registered '%s' D-Bus shell script(s)" % (len(self.scripts.keys())))
            self.log.debug("registered script(s): %s " % (", ".join(self.scripts.keys())))

            # Now send an event that indicates that the signature has changed.
            self._signatureChanged("")
        else:
            self.log.debug("the D-Bus shell script path '%s' does not exists! " % (self.script_path,))

    def _reload_signature(self, filename = None):
        """
        Reloads the signature for the given shell script.
        """

        # Prepare path values
        path = self.script_path
        filepath = (os.path.join(path, filename))

        # We cannot register dbus methods containing '.' so replace them.
        dbus_func_name = filename.replace(".","_")

        # Check if the file was removed or changed.
        if not os.path.exists(filepath) and filename in self.scripts:
            del(self.scripts[filename])
            self.log.debug("unregistered D-Bus shell script '%s'" % (filename,))

            try:
                method = getattr(self, dbus_func_name)
                self.unregister_dbus_method(method)
            except:
                raise
        else:

            # Check if the received filename is valid
            if not re.match(self.file_regex, filename):
                self.log.debug("skipped registering D-Bus shell script '%s', non-conform filename" % (filename))
            else:

                # ..is the file executable?
                if os.access(filepath, os.X_OK):

                    # Parse the script and if this was successful then add it te the list of known once.
                    data = self._parse_shell_script(filepath)
                    if data:
                        self.scripts[data[0]] = data
                        self.log.debug("registered D-Bus shell script '%s' signatures is: %s" % (data[0], data[1]))

                        # Dynamically register dbus methods here
                        def f(self, *args):
                            args = [filepath] + map(lambda x: str(x), args)

                            # Call the script with the --signature parameter
                            scall = Popen(args, stdout=PIPE, stderr=PIPE)
                            scall.wait()
                            return(scall.returncode,scall.stdout.read(),scall.stderr.read())

                        # Dynamically change the functions name and then register
                        # it as instance method to ourselves
                        setattr(f, '__name__', dbus_func_name)
                        setattr(self.__class__, dbus_func_name, f)
                        self.register_dbus_method(f, 'org.clacks', in_signature="ssss", out_signature=None)

                else:
                    self.log.debug("skipped registering D-Bus shell script '%s', it is not executable" % (filepath))

        # Reload the list of regsitered methods
        self.__reload_dbus_methods()

    def _parse_shell_script(self, path):
        """
        This method executes the given script (path) with the parameter
        '--signature' to receive the scripts signatur.

        It returns a tuple containing all found agruments and their type.
        """

        # Call the script with the --signature parameter
        try:
            scall = Popen([path, '--signature'], stdout=PIPE, stderr=PIPE)
            scall.wait()
        except OSError as e:
            self.log.info("failed to read signature from D-Bus shell script '%s' (%s) " % (path, str(e)))
            return

        # Check returncode of the script call.
        if scall.returncode != 0:
            self.log.info("failed to read signature from D-Bus shell script '%s' (%s) " % (path, scall.stderr.read()))

        # Check if we can read the returned signature.
        sig = {}
        try:
            # Signature was readable, now check if we got everything we need
            sig = loads(scall.stdout.read())
            if not(('in' in sig and type(sig['in']) == list) or 'in' not in sig):
                self.log.debug("failed to undertand in-signature of D-Bus shell script '%s'" % (path))
            elif 'out' not in sig or type(sig['out']) not in [str, unicode]:
                self.log.debug("failed to undertand out-signature of D-Bus shell script '%s'" % (path))
            else:
                return (os.path.basename(path), sig)
        except ValueError:
            self.log.debug("failed to undertand signature of D-Bus shell script '%s'" % (path))
        return None

    @dbus.service.method('org.clacks', in_signature='', out_signature='av')
    def shell_list(self):
        """
        Returns all availabe scripts and their signatures.
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
            raise NoSuchScriptException("unknown service %s" % cmd)

        # Execute the script and return the results
        args = map(lambda x: str(x), [os.path.join(self.script_path, cmd)] + args)
        res = Popen(args, stdout=PIPE, stderr=PIPE)
        res.wait()
        return ({'code': res.returncode,
                'stdout': res.stdout.read(),
                'stderr': res.stderr.read()})

    def register_dbus_method(self, func, dbus_interface, in_signature=None, out_signature=None):
        """
        Marks the given method as exported to the dbus.
        """

        # Validate the given DBus interface
        validate_interface_name(dbus_interface)

        # Dynamically create argument list
        args = []
        for arg in tuple(Signature(in_signature)):
            args.append("arg_"+str(arg)+"_"+str(len(args)))

        # Set DBus specific properties
        func._dbus_is_method = True
        func._dbus_async_callbacks = None
        func._dbus_interface = dbus_interface
        func._dbus_in_signature = in_signature
        func._dbus_out_signature = out_signature
        func._dbus_sender_keyword = None
        func._dbus_path_keyword = None
        func._dbus_rel_path_keyword = None
        func._dbus_destination_keyword = None
        func._dbus_message_keyword = None
        func._dbus_connection_keyword = None
        func._dbus_args = args
        func._dbus_get_args_options = {'byte_arrays': False,
                                       'utf8_strings': False}

    def unregister_dbus_method(self, method):
        """
        Unmarks the given method as exported to the dbus.
        """

        # Extract the function and its parameters
        func = method.__func__
        func._dbus_is_method = None
        func._dbus_async_callbacks = None
        func._dbus_interface = None
        func._dbus_in_signature = None
        func._dbus_out_signature = None

    def __reload_dbus_methods(self):
        """
        Reloads the list of exported dbus methods.
        This should be called once we've registered or unregistered
        a method to the dbus.
        """

        # Manually reload the list of registered methods.
        # Reset list first

        cname = self.__module__ + "." + self.__class__.__name__
        old_list = self._dbus_class_table[cname]['org.clacks']
        try:

            # Reload list
            for func in inspect.getmembers(self, predicate=inspect.ismethod):
                if getattr(func[1].__func__, '_dbus_interface', False):
                    self._dbus_class_table[cname]['org.clacks'][func[0]] = func[1].__func__

        # Restore the old method list if something goes wrong
        except Exception as e:
            self._dbus_class_table[cname]['org.clacks'] = old_list
            raise Exception("failed to manually register dbus method: %s" % (str(e),))

