#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import time
import logging
import pkg_resources
import codecs
import traceback
from random import randint

from setproctitle import setproctitle
from clacks.common import Environment
from clacks.client import __version__ as VERSION
from clacks.common.components.registry import PluginRegistry
from clacks.common.components.dbus_runner import DBusRunner
from clacks.common.network import Monitor
from clacks.common.event import EventMaker


def shutdown(a=None, b=None):
    global dr

    env = Environment.getInstance()
    log = logging.getLogger(__name__)

    # Function to shut down the client. Do some clean up and close sockets.
    amqp = PluginRegistry.getInstance("AMQPClientHandler")

    # Tell others that we're away now
    e = EventMaker()
    goodbye = e.Event(e.ClientLeave(e.Id(env.uuid)))
    if amqp:
        amqp.sendEvent(goodbye)

    # Shutdown plugins
    PluginRegistry.shutdown()

    #TODO: remove this hack
    wait = 1
    for t in env.threads:
        if t.isAlive():
            log.warning("thread %s still alive" % t.getName())
            if hasattr(t, 'stop'):
                log.warning("calling 'stop' for thread %s" % t.getName())
                t.stop()
            if hasattr(t, 'cancel'):
                log.warning("calling 'cancel' for thread %s" % t.getName())
                t.cancel()
            t.join(wait)

        if t.isAlive():
            try:
                log.warning("calling built in 'stop' for thread %s" % t.getName())
                t._Thread__stop()
            except:
                log.error("could not stop thread %s" % t.getName())

    dr.stop()

    log.info("shut down")
    logging.shutdown()


def handleTermSignal(a=None, b=None):
    """ Signal handler which will shut down the whole machinery """
    Environment.getInstance().active = False


def handleHupSignal(a=None, b=None):
    pass


def mainLoop(env):
    global netstate, dr

    # Enable DBus runner
    dr = DBusRunner()
    dr.start()

    """ Main event loop which will process all registerd threads in a loop.
        It will run as long env.active is set to True."""
    try:
        log = logging.getLogger(__name__)

        while True:

            # Check netstate and wait until we're back online
            if not netstate:
                log.info("waiting for network connectivity")
            while not netstate:
                time.sleep(1)

            # Load plugins
            PluginRegistry(component='client.module')

            # Sleep and slice
            wait = 2
            while True:
                # Threading doesn't seem to work well with python...
                for p in env.threads:

                    # Bail out if we're active in the meanwhile
                    if not env.active:
                        break

                    p.join(wait)

                # No break, go to main loop
                else:
                    continue

                # Break, leave main loop
                break

            # Break, leave main loop
            if not env.reset_requested:
                break

            # Wait for threads to shut down
            for t in env.threads:
                if hasattr(t, 'stop'):
                     t.stop()
                if hasattr(t, 'cancel'):
                     t.cancel()
                t.join(wait)

                #TODO: remove me
                if t.isAlive():
                    try:
                        t._Thread__stop()
                    except:
                        print(str(t.getName()) + ' could not be terminated')

            # Lets do an environment reset now
            PluginRegistry.shutdown()

            # Make us active and loop from the beginning
            env.reset_requested = False
            env.active = True

            if not netstate:
                log.info("waiting for network connectivity")
            while not netstate:
                time.sleep(1)

            sleep = randint(30, 60)
            env.log.info("waiting %s seconds to try an AMQP connection recovery" % sleep)
            time.sleep(sleep)

    except Exception as detail:
        log.critical("unexpected error in mainLoop")
        log.exception(detail)
        log.debug(traceback.format_exc())

    except KeyboardInterrupt:
        log.info("console requested shutdown")

    finally:
        shutdown()


def netactivity(online):
    global netstate
    if online:
        netstate = True

    else:
        env = Environment.getInstance()
        netstate = False

        # Function to shut down the client. Do some clean up and close sockets.
        amqp = PluginRegistry.getInstance("AMQPClientHandler")

        # Tell others that we're away now
        e = EventMaker()
        goodbye = e.Event(e.ClientLeave(e.Id(env.uuid)))
        if amqp:
            amqp.sendEvent(goodbye)

        env.reset_requested = True
        env.active = False

def main():
    """
    Main programm which is called when the clacks agent process gets started.
    It does the main forking os related tasks.
    """
    global netstate

    # Set process list title
    os.putenv('SPT_NOENV', 'non_empty_value')
    setproctitle("clacks-client")

    # Inizialize core environment
    env = Environment.getInstance()
    env.log.info("Clacks client is starting up")

    nm = Monitor(netactivity)
    netstate = nm.is_online()

    # Configured in daemon mode?
    if not env.config.get('client.foreground', default=env.config.get('core.foreground')):
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
            env.log.critical("Clacks client needs to be started as root in non foreground mode")
            exit(1)

        try:
            user = env.config.get("client.user")
            group = env.config.get("client.group")
            pidfile = env.config.get("client.pidfile",
                    default="/var/run/clacks/client.pid")

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
                env.log.warning("Clacks client should not be configured to run as root")

            context = daemon.DaemonContext(
                working_directory=env.config.get("client.workdir",
                    default=env.config.get("core.workdir")),
                umask=int(env.config.get("client.umask", default="2")),
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
                        pid_file = open(env.config.get('client.pidfile',
                            default="/var/run/clacks/client.pid"), 'w')
                        try:
                            pid_file.write(str(pid))
                        finally:
                            pid_file.close()
                    except IOError:
                        env.log.error("cannot write pid file %s" %
                                env.config.get('client.pidfile',
                                    default="/var/run/clacks/client.pid"))
                        exit(1)

                    mainLoop(env)

            except daemon.daemon.DaemonOSEnvironmentError as detail:
                env.log.critical("error while daemonizing: " + str(detail))
                exit(1)

    else:
        mainLoop(env)


if __name__ == '__main__':
    if not sys.stdout.encoding:
        sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    if not sys.stderr.encoding:
        sys.stderr = codecs.getwriter('utf8')(sys.stderr)

    pkg_resources.require('clacks.common==%s' % VERSION)

    netstate = False
    main()
