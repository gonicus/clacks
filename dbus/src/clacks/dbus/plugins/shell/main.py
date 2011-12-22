import dbus.service
from clacks.common import Environment
from clacks.common.components import Plugin
from clacks.dbus import get_system_bus

#TODO: this module is in the works

class DBusShellHandler(dbus.service.Object, Plugin):
    """ Shell handler, exporting shell commands to the bus """

    def __init__(self):
        conn = get_system_bus()
        dbus.service.Object.__init__(self, conn, '/org/clacks/shell')
        self.env = Environment.getInstance()

    @dbus.service.method('org.clacks', in_signature='', out_signature='')
    def get_signatures(self):
        pass
