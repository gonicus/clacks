import re
import os
import dbus.service
from subprocess import Popen, PIPE
from clacks.common import Environment
from clacks.common.components import Plugin
from clacks.dbus import get_system_bus


class DBusShellException(Exception):
    pass


class NoSuchScriptException(DBusShellException):
    """
    Exception thrown for unknown services
    """
    pass


class DBusShellHandler(dbus.service.Object, Plugin):
    """ Shell handler, exporting shell commands to the bus """

    script_path = None

    def __init__(self):
        conn = get_system_bus()
        dbus.service.Object.__init__(self, conn, '/org/clacks/shell')
        self.env = Environment.getInstance()
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

        # Set defaults.
        author = date = version = "unknown"
        params = []

        # Walk through script lines and extract usefull information
        contents = open(path).read()
        lines = contents.split("\n")
        line = ""
        while len(lines) and re.match("^(#.*|[ \s]*)$", line):
            line = lines.pop(1)

            # Extract author, version and date from the script
            if re.match(".*author[\s]*:.*", line, re.IGNORECASE):
                author = re.sub(".*author[\s]*:[\s]*(.*)", "\\1", line, 0,re.IGNORECASE).strip()
            if re.match(".*date[\s]*:.*", line, re.IGNORECASE):
                date = re.sub(".*date[\s]*:[\s]*(.*)", "\\1", line, 0,re.IGNORECASE).strip()
            if re.match(".*version[\s]*:.*", line, re.IGNORECASE):
                version = re.sub(".*version[\s]*:[\s]*(.*)", "\\1", line, 0,re.IGNORECASE).strip()

            # Extract script parameters
            if re.match(".*param[\s]*:.*", line, re.IGNORECASE):
                try:
                    pname, ptype, pdesc = re.match(".*param[\s]*:[\s]*([^\(]*)\(([^\(])\)[\s]*;[\s]*(.*)[\s]*$", line, re.IGNORECASE).groups()
                    params.append((pname, ptype, pdesc))
                except:
                    raise DBusShellException("Failed to parse parameter list of '%s'!" % (path))

        # Return the extracted script data.
        return (os.path.basename(path), author, date, version, params)

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

        #TODO: Check parameters

        # Execute the script and return the results
        args = map(lambda x: str(x), [os.path.join(self.script_path ,cmd)] + args)
        res = Popen(args, stdout=PIPE, stderr=PIPE)
        res.wait()
        return ({'code': res.returncode,
                'stdout': res.stdout.read(),
                'stderr': res.stderr.read()})
