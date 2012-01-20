# -*- coding: utf-8 -*-
import dbus
from clacks.common.components import Plugin
from clacks.common.components import Command
from clacks.common import Environment


class Notify(Plugin):
    """
    Clacks Client Notification Plugin
    =================================

    This plugin allows to send notification to a user or a list of users.

    e.g.:

    >>> proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "notify", "user1", "Hallo", "This is a message")

    >>> proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "notify_all", "Hallo", "This is a message")

    """

    _target_ = 'notify'

    def __init__(self):
        env = Environment.getInstance()
        self.env = env

    @Command()
    def notify(self, user, title, message,
        timeout=0,
        urgency="normal",
        icon="dialog-information",
        actions="",
        recurrence=60):

        """ Sent a notification to a given user """

        # Get BUS connection
        bus = dbus.SystemBus()
        clacks_dbus = bus.get_object('org.clacks',
                                   '/org/clacks/notify')

        # Send notification and keep return code
        o = clacks_dbus._notify(user, title, message, timeout, urgency,
            icon, actions, recurrence, dbus_interface="org.clacks")
        return(int(o))

    @Command()
    def notify_all(self, title, message,
        timeout=0,
        urgency="normal",
        icon="dialog-information",
        actions="",
        recurrence=60):

        """ Sent a notification to all users on a machine """

        # Get BUS connection
        bus = dbus.SystemBus()
        clacks_dbus = bus.get_object('org.clacks',
                                   '/org/clacks/notify')

        # Send notification and keep return code
        o = clacks_dbus._notify_all(title, message, timeout, urgency,
            icon, actions, recurrence, dbus_interface="org.clacks")
        return(int(o))
