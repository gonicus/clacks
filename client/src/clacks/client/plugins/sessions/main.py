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
.. _client-session:

Session trigger
===============

To. Do.
"""

import gobject #@UnusedImport
import pwd
import zope.event
from dateutil.parser import parse
from clacks.common.components import Plugin
from clacks.common.components import Command
from clacks.common.components.registry import PluginRegistry
from clacks.common.components.dbus_runner import DBusRunner
from clacks.common import Environment
from clacks.common.event import EventMaker
from zope.interface import implements
from clacks.common.handler import IInterfaceHandler
from clacks.client.event import Resume


class SessionKeeper(Plugin):
    """
    Utility class that contains methods needed to handle WakeOnLAN
    functionality.
    """
    implements(IInterfaceHandler)
    _priority_ = 99
    _target_ = 'session'
    __sessions = {}
    __callback = None
    active = False

    def __init__(self):
        env = Environment.getInstance()
        self.env = env
        self.__dr = DBusRunner.get_instance()
        self.__bus = None

        # Register for resume events
        zope.event.subscribers.append(self.__handle_events)

    @Command()
    def getSessions(self):
        """ Return the list of active sessions """
        return self.__sessions

    def serve(self):
        self.__bus = self.__dr.get_system_bus()

        # Trigger session update
        self.__update_sessions()

        # register a signal receiver
        self.__bus.add_signal_receiver(self.event_handler,
            dbus_interface="org.freedesktop.ConsoleKit.Seat",
            message_keyword='dbus_message')

        # Trigger session update
        self.__update_sessions()

    def stop(self):
        if self.__bus:
            self.__bus.remove_signal_receiver(self.event_handler,
                dbus_interface="org.freedesktop.ConsoleKit.Seat",
                message_keyword='dbus_message')

    def __handle_events(self, event):
        if isinstance(event, Resume):
            self.__update_sessions()

    def event_handler(self, msg_string, dbus_message):
        self.__update_sessions()

        if self.__callback:
            #pylint: disable=E1102
            self.__callback(dbus_message.get_member(), msg_string)

    def __update_sessions(self):
        obj = self.__bus.get_object("org.freedesktop.ConsoleKit",
            "/org/freedesktop/ConsoleKit/Manager")
        sessions = {}

        for session_name in obj.GetSessions():
            session_o = self.__bus.get_object("org.freedesktop.ConsoleKit",
                session_name)

            uid = pwd.getpwuid(int(session_o.GetUser())).pw_name
            sessions[str(session_name).split("/")[-1]] = {
                "uid": uid,
                "active": bool(session_o.IsActive()),
                "created": parse(str(session_o.GetCreationTime())),
                "display": str(session_o.GetX11Display()),
            }

        self.__sessions = sessions
        self.sendSessionNotification()

    def sendSessionNotification(self):
        # Build event
        amqp = PluginRegistry.getInstance("AMQPClientHandler")
        e = EventMaker()
        more = set([x['uid'] for x in self.__sessions.values()])
        more = map(e.Name, more)
        info = e.Event(
            e.UserSession(
                e.Id(self.env.uuid),
                e.User(*more)))

        amqp.sendEvent(info)
