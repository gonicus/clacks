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

"""
 Clacks Shell
 ------------

 There are three usage scenarios:

 1) Interactive: Let's you execute code interactively.

     Usage:
       clacksh [-u/--user username] [-p/--password passwort]
           [service-uri]

 2) One-Shot: Executes code1...code2 and returns.

     Usage:
        clacksh [-u/--user username] [-p/--password passwort]
            [-c/--command 'cmd;cmd;...'] [service-uri]

 3) Script: Write a script and execute it.

     Usage:
        cat YourScript | clacksh [-u/--user username]
            [-p/--password passwort] [service-uri]

 The code you can execute is basically Python code. There is a special object
 named "clacks" that gives you access to all supported Clacks services - which are
 mapped to the global namespace, additionally. Try
 clacks.help() for a list of methods.
"""
import sys
import re
import traceback
import code
import getopt
import socket
import getpass
import logging
import readline #@UnusedImport
import gettext
import textwrap
import locale
import thread
import qpid.messaging
from urllib2 import HTTPError
from pkg_resources import resource_filename #@UnresolvedImport
from dbus.exceptions import DBusException

from clacks.common.components import AMQPServiceProxy
from clacks.common.components import JSONServiceProxy, JSONRPCException
from clacks.common.components.zeroconf_client import ZeroconfClient
from clacks.common.utils import parseURL

# Set locale domain
t = gettext.translation('messages', resource_filename("clacks.shell", "locale"), fallback=True)
_ = t.ugettext


# Global lock
a_lock = thread.allocate_lock()


def softspace(fn, newvalue):
    """ Method copied from imported code """
    oldvalue = 0
    try:
        oldvalue = fn.softspace
    except AttributeError:
        pass
    try:
        fn.softspace = newvalue
    except (AttributeError, TypeError):
        # "attribute-less object" or "read-only attributes"
        pass
    return oldvalue


class MyConsole(code.InteractiveConsole):
    """ MyConsole Subclass of code.InteractiveConsole """

    # Stores the last code executed.
    lastCode = None

    def getLastCode(self):
        """ Put the last executed code object"""
        return self.lastCode

    def runcode(self, code):
        """
        Execute a code object.

        When an exception occurs, self.showtraceback() is called to
        display a traceback.  All exceptions are caught except
        SystemExit, which is reraised.

        A note about KeyboardInterrupt: this exception may occur
        elsewhere in this code, and may not always be caught.  The
        caller should be prepared to deal with it.
        """
        self.lastCode = code
        try:
            exec code in self.locals
        except SystemExit:
            raise
        except HTTPError as e:
            if e.code == 401:
                raise
            self.showtraceback()
        except JSONRPCException as e:
            # Check for error member
            try:
                err = e.error["error"]
            except TypeError:
                err = str(e)

            # Resolve error details if supplied
            error_id = re.match(r'^<([^>]+)>.*$', err)
            if error_id:
                locs = locale.getdefaultlocale()
                info = self.proxy.get_error(error_id.groups()[0], ".".join(locs if locs != (None, None) else ("en", "US")))
                detail = ""
                if info['details']:
                    detail = " - %s [%s]" % (info['details'][0]['detail'], info['details'][0]['index'])
                if info['topic']:
                    print info['text'] + detail + ": " + info['topic']
                else:
                    print info['text'] + detail

            else:
                print err

            if softspace(sys.stdout, 0):
                print
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info() #@UnusedVariable
            self.showtraceback()
        else:
            if softspace(sys.stdout, 0):
                print


class ClacksService():
    """ The ClacksService class encapsulates all Clacks functionality that is
        accessible via the interactive console. """
    proxy = None

    def __init__(self):
        self.name = 'ClacksService'
        self.domain = socket.getfqdn().split('.', 1)[1]

    def connect(self, service_uri='', username='', password=''):
        """ Creates a service proxy object from the arguments. """

        # Clean arguments
        username = username.strip()
        password = password.strip()
        service_uri = service_uri.strip()

        if len(service_uri) <= 0:
            print _("Searching service provider...")
            try:
                service_uri = ZeroconfClient.discover(['_amqps._tcp', '_amqp._tcp',
                    '_https._tcp', '_http._tcp'], domain=self.domain)[0]

            except DBusException as e:
                print _("DBUS error: %s") % str(e)
                sys.exit(1)

            except Exception as e:
                print e.__dict__

        # Test if one argument is still needed.
        if len(service_uri) <= 0:
            tmp = service_uri
            service_uri = raw_input('Service URI: [%s]' % service_uri).strip()
            if len(service_uri) <= 0:
                service_uri = tmp

        # Chek if URL is parsable
        url = parseURL(service_uri)

        # If we have still no service host, quit, because the connect will fail
        # pylint: disable-msg=E1101
        if not url:
            print _("Need at least a service URI!")
            sys.exit(1)

        # TRANSLATOR: Conected to URL, i.e. https://amqp.local:8080/rpc
        print _("Connected to %s://%s:%s/%s") % (url['scheme'], url['host'], url['port'], url['path'])

        # Check weather to use method parameters or the URI elements.
        # If URI username is set and the method username is not set
        if url['user']:
            username = url['user']
        # If URI password is set and the username is set and the method password is not set
        if url['password']:
            password = url['password']

        # If we have still no credentials query for them
        if len(username) <= 0:
            # TRANSLATOR: This is a prompt - Username [joe]:
            username = raw_input(_("Username") + " [%s]: " % getpass.getuser()).strip()
            if len(username) <= 0:
                username = getpass.getuser()

        if len(password) <= 0:
            # TRANSLATOR: This is a prompt - Password:
            password = getpass.getpass(_("Password") + ': ')

        # Create service proxy
        if url['scheme'][0:4] == "amqp":
            connection = '%s://%s:%s@%s:%s/%s' % (
                url['scheme'],
                username,
                password,
                url['host'],
                url['port'],
                url['path'])

            try:
                self.proxy = AMQPServiceProxy(connection)
            except qpid.messaging.exceptions.ConnectionError:
                print _("Login of user '%s' failed") % username
                sys.exit(1)

        # Default and HTTP
        elif url['scheme'][0:4] == "http":
            connection = '%s://%s:%s/%s' % (
                url['scheme'],
                url['host'],
                url['port'],
                url['path'])
            self.proxy = JSONServiceProxy(connection)

        else:
            print _("The selected protocol is not supported!")
            sys.exit(1)

        # Try to log in
        try:
            if not self.proxy.login(username, password):
                print _("Login of user '%s' failed") % username
                sys.exit(1)
        except Exception, e:
            print e
            sys.exit(1)

        return connection, username, password

    def reconnectJson(self, connection, username, password):
        self.proxy = JSONServiceProxy(connection)
        try:
            if self.proxy.login(username, password):
                pass
            else:
                sys.exit(1)
        except Exception, e:
            print e
            sys.exit(1)

    def help(self):
        """ Prints some help """
        mlist = {}
        loc = locale.getdefaultlocale()
        try:
            loc = ".".join(loc)
        except TypeError:
            loc = None

        for method, info in self.proxy.getMethods(None, loc).iteritems():
            # Get the name of the module.
            module = info['target']
            if module not in mlist:
                mlist[module] = []

            sig = info['sig']
            args = ', '.join(sig)
            doc = ""
            if info['doc'] != None:
                d = ' '.join(info['doc'].split())
                for line in textwrap.wrap(d, 72):
                    doc += "    %s\n" % line
            mlist[module].append((method, args, doc))

        keylist = mlist.keys()
        keylist.sort()
        for module in keylist:
            print module.upper()
            print "=" * len(module)
            mlist[module].sort()
            for mset in mlist[module]:
                print "  %s(%s)\n%s" % mset


def main(argv=sys.argv):

    # Print help/usage and exit
    if '-h' in argv or '--help' in argv:
        print __doc__
        return 0
    try:
        opts, args = getopt.getopt(argv[1:], "u:p:c:", ["user=", "password=", "command="])
    except getopt.GetoptError:
        print __doc__
        sys.exit(2)

    service_uri = ''
    username = ''
    password = ''
    command = ''

    if len(args) >= 1:
        service_uri = args[0]

    for opt, arg in opts:
        if opt in ("-u", "--user"):
            username = arg
        elif opt in ("-p", "--password"):
            password = arg
        elif opt in ("-c", "--command"):
            command = arg

    # Create service object
    service = ClacksService()

    # Check if connection could be established
    try:
        service_uri, username, password = service.connect(service_uri, username, password)
    except KeyboardInterrupt:
        print
        sys.exit(1)

    # Prepare to enter the interactive console.
    # Make the the ClacksService instance available to the console via the
    # "clacks" object.
    service.proxy.help = service.help
    context = {'clacks': service.proxy, '__name__': '__console__', '__doc__': None}

    # This python wrap string catches any exception, prints it and exists the
    # program with a failure that can be processed by the caller (e.g. on a
    # command line).
    wrap = """
import sys, traceback
try:
    %s
except:
    traceback.print_exc()
    sys.exit(1)
"""
    startup = """
import readline
import rlcompleter
import atexit
import os

# Tab completion
readline.parse_and_bind('tab: complete')

# history file
histfile = os.path.join(os.environ['HOME'], '.clacks.history')
try:
    readline.read_history_file(histfile)
except IOError:
    pass
atexit.register(readline.write_history_file, histfile)
del os, histfile, readline, rlcompleter

for i in clacks.getMethods().keys():
    globals()[i] = getattr(clacks, i)
"""

    # Use script mode:
    if not sys.stdin.isatty():
        pyconsole = code.InteractiveInterpreter(context)
        try:
            cake = sys.stdin.read()
            pyconsole.runcode(cake)
            letRun = 0
        except Exception:
            traceback.print_exc()
            return 1
    # Use one-shot mode
    elif len(argv) >= 5:
        pyconsole = code.InteractiveInterpreter(context)
        try:
            commands = command.split(';')
            for cake in commands:
                if not cake:
                    continue

                pyconsole.runcode(wrap % cake)
            letRun = 0
        except Exception:
            return 1
    # Use interactive mode
    else:
        letRun = 1
        pyconsole = None
        while(letRun):
            try:
                if not pyconsole:
                    pyconsole = MyConsole(context)
                    pyconsole.proxy = service.proxy
                    pyconsole.runcode(startup)
                    pyconsole.interact(_("Clacks infrastructure shell. Use Ctrl+D to exit."))
                else:
                    mycode = pyconsole.getLastCode()
                    pyconsole = MyConsole(context)
                    pyconsole.proxy = service.proxy
                    pyconsole.runcode(mycode)
                    pyconsole.interact("")

                print _("Closing session")
                service.proxy.logout()
                letRun = 0

            # In case of a clacks-agent restart we have to double check login
            except HTTPError as e:
                if e.code == 401:
                    service.reconnectJson(service_uri, username, password)
                    context = {'clacks': service, 'service': service.proxy,
                        '__name__': '__console__', '__doc__': None}
                else:
                    print e
                    sys.exit(1)
    return 0

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s (%(levelname)s): %(message)s')
    sys.exit(main())
