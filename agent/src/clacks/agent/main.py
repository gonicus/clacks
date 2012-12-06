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
import logging
import pkg_resources
import codecs
from setproctitle import setproctitle
from clacks.common import Environment
from clacks.common.utils import SystemLoad
from clacks.common.event import EventMaker
from clacks.common.components import ObjectRegistry, PluginRegistry
from clacks.common.components.dbus_runner import DBusRunner
from clacks.agent import __version__ as VERSION


def shutdown(a=None, b=None):
    """ Function to shut down the agent. Do some clean up and close sockets."""
    global dr

    amqp = PluginRegistry.getInstance("AMQPHandler")

    # Tell others that we're away now
    if hasattr(amqp, 'env'):
        e = EventMaker()
        goodbye = e.Event(e.NodeLeave(e.Id(amqp.env.id)))
        amqp.sendEvent(goodbye)

    # Shutdown plugins
    PluginRegistry.shutdown()
    dr.stop()

    logging.info("shut down")
    logging.shutdown()


def handleTermSignal(a=None, b=None):
    """ Signal handler which will shut down the whole machinery """
    Environment.getInstance().active = False


def handleHupSignal(a=None, b=None):
    pass


def mainLoop(env):
    """ Main event loop which will process all registerd threads in a loop.
        It will run as long env.active is set to True."""

    global dr

    # Enable DBus runner
    dr = DBusRunner()
    dr.start()
    log = logging.getLogger(__name__)

    try:
        while True:
                # Load plugins
                oreg = ObjectRegistry.getInstance() #@UnusedVariable
                pr = PluginRegistry() #@UnusedVariable
                cr = PluginRegistry.getInstance("CommandRegistry")
                amqp = PluginRegistry.getInstance("AMQPHandler")
                index = PluginRegistry.getInstance("ObjectIndex")

                wait = 2
                notifyInterval = 10
                interval = notifyInterval
                loadAvg = SystemLoad()

                # Sleep and slice
                while True:

                    # Threading doesn't seem to work well with python...
                    for p in env.threads:

                        # Bail out if we're active in the meanwhile
                        if not env.active:
                            break

                        # Check if we reached the notification interval
                        interval += wait
                        if interval > notifyInterval:
                            interval = 0
                            load = loadAvg.getLoad()
                            latency = 0
                            workers = len(env.threads)
                            log.debug("load %s, latency %s, workers %s" %
                                    (load, latency, workers))

                            e = EventMaker()
                            status = e.Event(
                                e.NodeStatus(
                                    e.Id(env.id),
                                    e.Load(str(load)),
                                    e.Latency(str(latency)),
                                    e.Workers(str(workers)),
                                    e.Indexed("true" if index.index_active() else
                                        "false"),
                                )
                            )
                            amqp.sendEvent(status)

                        # Disable potentially dead nodes
                        cr.updateNodes()

                        p.join(wait)

                    # No break, go to main loop
                    else:
                        continue

                    # Leave the thread loop
                    break

                # Break, leave main loop
                if not env.reset_requested:
                    break

                # Wait for threads to shut down
                for t in env.threads:
                    t.join(wait)
                    if hasattr(t, 'stop'):
                        t.stop()

                # Lets do an environment reset now
                PluginRegistry.shutdown()

                # Make us active and loop from the beginning
                env.reset_requested = False
                env.active = True

    # Catchall, pylint: disable=W0703
    except Exception as detail:
        log.critical("unexpected error in mainLoop")
        log.exception(detail)

    except KeyboardInterrupt:
        log.info("console requested shutdown")

    finally:
        shutdown()


def main():
    """ Main programm which is called when the clacks agent process gets started.
        It does the main forking os related tasks. """

    # Set process list title
    os.putenv('SPT_NOENV', 'non_empty_value')
    setproctitle("clacks-agent")

    # Inizialize core environment
    env = Environment.getInstance()
    if not env.base:
        env.log.critical("Clacks agent needs a 'core.base' do operate on")
        exit(1)

    env.log.info("Clacks %s is starting up (server id: %s)" % (VERSION, env.id))

    if env.config.get('core.profile'):
        import cProfile
        import clacks.common.lsprofcalltree
        p = cProfile.Profile()
        p.runctx('mainLoop(env)', globals(), {'env': env})
        #pylint: disable=E1101
        k = clacks.common.lsprofcalltree.KCacheGrind(p)
        data = open('prof.kgrind', 'w+')
        k.output(data)
        data.close()
    else:
        mainLoop(env)


if __name__ == '__main__':
    if not sys.stdout.encoding:
        sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    if not sys.stderr.encoding:
        sys.stderr = codecs.getwriter('utf8')(sys.stderr)

    pkg_resources.require('clacks.common==%s' % VERSION)
    main()
