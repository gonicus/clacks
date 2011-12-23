# -*- coding: utf-8 -*-
"""
Overview
========

The *DBUS* module bundles the GOsa DBUS daemon and a couple code modules
needed to run it. The DBUS itself is meant to be extended by implementing
:class:`dbus.service.Object` and additionally inherit from
:class:`clacks.common.components.plugin.Plugin`.
When starting up the system, the DBUS components looks for plugins in the setuptools
system and registers them into to the :class:`clacks.common.components.registry.PluginRegistry`.

This happens automatically depending on what's registered on the
``[dbus.module]`` setuptools entrypoint.

To provide services it registers the system bus ``org.clacks`` to the
systems DBUS, exposing functionality to the outside world.

All the DBUS plugins you provide run as *root*, so the service is meant as
a gateway to call functionality which needs more administrative power than
the GOsa client user has.

Code example::

    import dbus.service
    import subprocess
    from clacks.common import Environment
    from clacks.common.components import Plugin
    from clacks.dbus import get_system_bus


    class DBusWakeOnLanHandler(dbus.service.Object, Plugin):
        \"\"\" WOL handler, exporting shell commands to the bus \"\"\"

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

This one will provide wake-on-lan functionality over DBUS.

If you're looking for documentation on how to write plugins, please take a look
at the :ref:`Plugin section<plugins>`.
"""
__version__ = __import__('pkg_resources').get_distribution('clacks.dbus').version
__import__('pkg_resources').declare_namespace(__name__)

from clacks.dbus.utils import get_system_bus
