#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
    global dr

    """ Function to shut down the agent. Do some clean up and close sockets."""
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

    try:
        log = logging.getLogger(__name__)

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

    # Configured in daemon mode?
    if not env.config.get('core.foreground'):
        import grp
        import pwd
        import stat
        import signal
        import daemon
        import lockfile
        from lockfile import AlreadyLocked, LockFailed

        pidfile = None

        # Running as root?
        if os.geteuid() != 0:
            env.log.critical("Clacks agent needs to be started as root in non foreground mode")
            exit(1)

        try:
            user = env.config.get("core.user")
            group = env.config.get("core.group")

            pidfile = env.config.get("core.pidfile", default="/var/run/clacks/clacks-agent.pid")

            # Check if pid path if writable for us
            piddir = os.path.dirname(pidfile)
            pwe = pwd.getpwnam(user)
            gre = grp.getgrnam(group)
            try:
                s = os.stat(piddir)
            except OSError as e:
                env.log.critical("cannot stat pid directory '%s' - %s" % (piddir, str(e)))
                exit(1)
            mode = s[stat.ST_MODE]

            if not bool(((s[stat.ST_UID] == pwe.pw_uid) and (mode & stat.S_IWUSR)) or \
                   ((s[stat.ST_GID] == gre.gr_gid) and (mode & stat.S_IWGRP)) or \
                   (mode & stat.S_IWOTH)):
                env.log.critical("cannot aquire lock '%s' - no write permission for group '%s'" % (piddir, group))
                exit(1)

            # Has to run as root?
            if pwe.pw_uid == 0:
                env.log.warning("Clacks agent should not be configured to run as root")

            context = daemon.DaemonContext(
                working_directory=env.config.get("core.workdir"),
                umask=int(env.config.get("core.umask")),
                pidfile=lockfile.FileLock(pidfile),
            )

            context.signal_map = {
                signal.SIGTERM: handleTermSignal,
                signal.SIGHUP: handleHupSignal,
            }

            context.uid = pwd.getpwnam(user).pw_uid
            context.gid = grp.getgrnam(group).gr_gid

        except KeyError:
            env.log.critical("cannot resolve user:group '%s:%s'" %
                (user, group))
            exit(1)

        except AlreadyLocked:
            env.log.critical("pid file '%s' is already in use" % pidfile)
            exit(1)

        except LockFailed:
            env.log.critical("cannot aquire lock '%s'" % pidfile)
            exit(1)

        else:

            try:
                with context:
                    # Write out pid to allow clean shutdown
                    pid = os.getpid()
                    env.log.debug("forked process with pid %s" % pid)

                    try:
                        pid_file = open(env.config.get('core.pidfile'), 'w')
                        try:
                            pid_file.write(str(pid))
                        finally:
                            pid_file.close()
                    except IOError:
                        env.log.error("cannot write pid file %s" %
                                env.config.get('core.pidfile'))
                        exit(1)

                    mainLoop(env)

            except daemon.daemon.DaemonOSEnvironmentError as detail:
                env.log.critical("error while daemonizing: " + str(detail))
                exit(1)

    else:
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
