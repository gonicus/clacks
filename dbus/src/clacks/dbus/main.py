#!/usr/bin/env python
# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

import os
import sys
import pkg_resources
import codecs
import traceback
import gobject
import dbus.mainloop.glib
import logging

from setproctitle import setproctitle
from clacks.common import Environment
from clacks.dbus import __version__ as VERSION
from clacks.common.components.registry import PluginRegistry
from clacks.dbus import get_system_bus

loop = None


def shutdown(a=None, b=None):
    """ Function to shut down the client. """
    global loop

    env = Environment.getInstance()
    env.log.info("Clacks DBUS is shutting down")

    # Shutdown plugins
    PluginRegistry.shutdown()
    if loop:
        loop.quit()

    logging.shutdown()
    exit(0)


def mainLoop(env):
    global loop

    log = logging.getLogger(__name__)

    try:
        # connect to dbus and setup loop
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        get_system_bus()

        # Instanciate dbus objects
        PluginRegistry(component='dbus.module')

        # Enter main loop
        loop = gobject.MainLoop()
        loop.run()

    except Exception as detail:
        log.critical("unexpected error in mainLoop")
        log.exception(detail)
        log.debug(traceback.format_exc())

    finally:
        shutdown()


def main():
    """ Main programm which is called when the clacks agent process gets started.
        It does the main forking os related tasks. """

    # Set process list title
    os.putenv('SPT_NOENV', 'non_empty_value')
    setproctitle("clacks-dbus")

    # Inizialize core environment
    env = Environment.getInstance()
    env.log.info("Clacks DBUS is starting up")

    # Are we root?
    if os.geteuid() != 0:
        env.log.critical("Clacks DBUS must be run as root")
        exit(1)

    mainLoop(env)


if __name__ == '__main__':
    if not sys.stdout.encoding:
        sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    if not sys.stderr.encoding:
        sys.stderr = codecs.getwriter('utf8')(sys.stderr)

    pkg_resources.require('clacks.common==%s' % VERSION)

    main()
