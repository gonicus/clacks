import dbus.service
import subprocess
from clacks.common import Environment
from clacks.common.components import Plugin
from clacks.dbus import get_system_bus


class DBusWakeOnLanHandler(dbus.service.Object, Plugin):
    """ WOL handler, exporting shell commands to the bus """

    def __init__(self):
        conn = get_system_bus()
        dbus.service.Object.__init__(self, conn, '/org/clacks/wol')
        self.env = Environment.getInstance()

    @dbus.service.method('org.clacks', in_signature='s', out_signature='')
    def wakeOnLan(self, mac):
        p = subprocess.Popen([r"wakeonlan", mac])
        p.wait()
        # return exit code, unfortunately wakeonlan returns 0
        # even when an error occurs :(
        return p.returncode
