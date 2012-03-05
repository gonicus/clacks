"""
Clacks Client Notification Plugin
=================================

This plugin allows to send notification to a user or a list of users.

e.g.:

>>> proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "notify", "user1", "Hallo", "This is a message")

>>> proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "notify_all", "Hallo", "This is a message")

"""

# -*- coding: utf-8 -*-
import dbus
import logging
from clacks.common.components import PluginRegistry
from clacks.common.components import Plugin
from clacks.common.components import Command
from clacks.common import Environment


class Notify(Plugin):
    _target_ = 'notify'
    bus = None
    clacks_dbus = None

    def __init__(self):
        env = Environment.getInstance()
        self.env = env
        self.log = logging.getLogger(__name__)

        # Register ourselfs for bus changes on org.clacks
        self.bus = dbus.SystemBus()
        self.bus.watch_name_owner("org.clacks", self.__dbus_proxy_monitor)

    def __dbus_proxy_monitor(self, bus_name):
        """
        This method monitors the DBus service 'org.clacks' and whenever there is a
        change in the status (dbus closed/startet) we will take notice.
        And can register or unregister methods to the dbus
        """
        if "org.clacks" in self.bus.list_names():
            if self.clacks_dbus:
                del(self.clacks_dbus)
            self.clacks_dbus = self.bus.get_object('org.clacks', '/org/clacks/notify')
            ccr = PluginRegistry.getInstance('ClientCommandRegistry')
            ccr.register("notify", 'Notify.notify', [], \
                    ['user','title','message','timeout','urgency','icon','actions','recurrence'], \
                    'Sent a notification to a given user')
            ccr.register("notify_all", 'Notify.notify_all', [], \
                    ['title','message','timeout','urgency','icon','actions','recurrence'], \
                    'Sent a notification to a given user')
            amcs = PluginRegistry.getInstance('AMQPClientService')
            amcs.reAnnounce()
            self.log.info("established dbus connection")

        else:
            if self.clacks_dbus:
                del(self.clacks_dbus)

                # Trigger resend of capapability event
                ccr = PluginRegistry.getInstance('ClientCommandRegistry')
                ccr.unregister("notify")
                ccr.unregister("notify_all")
                amcs = PluginRegistry.getInstance('AMQPClientService')
                amcs.reAnnounce()
                self.log.info("lost dbus connection")
            else:
                self.log.info("no dbus connection")

    def notify(self, user, title, message,
        timeout=0,
        urgency="normal",
        icon="dialog-information",
        actions="",
        recurrence=60):

        """ Sent a notification to a given user """

        # Send notification and keep return code
        o = self.clacks_dbus._notify(user, title, message, timeout, urgency,
            icon, actions, recurrence, dbus_interface="org.clacks")
        return(int(o))

    def notify_all(self, title, message,
        timeout=0,
        urgency="normal",
        icon="dialog-information",
        actions="",
        recurrence=60):

        """ Sent a notification to all users on a machine """

        # Send notification and keep return code
        o = self.clacks_dbus._notify_all(title, message, timeout, urgency,
            icon, actions, recurrence, dbus_interface="org.clacks")
        return(int(o))
