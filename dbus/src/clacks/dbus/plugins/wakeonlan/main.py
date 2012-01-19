"""
Clacks D-Bus Wake on lan
^^^^^^^^^^^^^^^^^^^^^^^^

This Clacks-DBus plugin provides wake on lan functionality.

>>> proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "dbus_wake_on_lan", "<mac>")
"""


import dbus.service
import subprocess
from clacks.common import Environment
from clacks.common.components import Plugin
from clacks.dbus import get_system_bus


class DBusWakeOnLanHandler(dbus.service.Object, Plugin):
    """
    This Clacks-DBus plugin provides wake on lan functionality.
    """
    def __init__(self):
        conn = get_system_bus()
        dbus.service.Object.__init__(self, conn, '/org/clacks/wol')
        self.env = Environment.getInstance()

    @dbus.service.method('org.clacks', in_signature='s', out_signature='')
    def wake_on_lan(self, mac):
        p = subprocess.Popen([r"wakeonlan", mac])
        p.wait()
        # return exit code, unfortunately wakeonlan returns 0
        # even when an error occurs :(
        return p.returncode
