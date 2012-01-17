# -*- coding: utf-8 -*-
import dbus.service
from clacks.common import Environment
from clacks.common.components import Plugin
from clacks.dbus import get_system_bus
import sys
import traceback
import subprocess


class DBusNotifyHandler(dbus.service.Object, Plugin):
    """ Notify handler, sends user notifications """

    def __init__(self):
        conn = get_system_bus()
        dbus.service.Object.__init__(self, conn, '/org/clacks/notify')
        self.env = Environment.getInstance()

    @dbus.service.method('org.clacks', in_signature='ssisssi', out_signature='i')
    def _notify_all(self, title, message, timeout, urgency, icon, actions, recurrence):
        """
        Try to send a notification to all users on a machine user using the 'notify-user' script.
        """
        return(self.call(message=message, title=title, broadcast=True, timeout=timeout,
            urgency=urgency, icon=icon, recurrence=recurrence, actions=actions))

    @dbus.service.method('org.clacks', in_signature='sssisssi', out_signature='i')
    def _notify(self, user, title, message, timeout, urgency, icon, actions, recurrence):
        """
        Try to send a notification to a user using the 'notify-user' script.
        """
        return(self.call(message=message, title=title, user=user, timeout=timeout,
            urgency=urgency, icon=icon, recurrence=recurrence, actions=actions))

    def call(self, message, title,
        user="",
        broadcast=False,
        timeout=120,
        actions="",
        urgency="normal",
        icon="dialog-information",
        recurrence=60):

        try:

            # Build up the subprocess command
            # and add parameters on demand.
            cmd = ["notify-user"]
            cmd += [title]
            cmd += [message]

            if broadcast:
                cmd += ["--broadcast"]
            else:
                cmd += ["--user"]
                cmd += [str(user)]

            if icon:
                cmd += ["--icon"]
                cmd += [str(icon)]

            if actions:
                cmd += ["--actions"]
                cmd += [str(actions)]

            if urgency:
                cmd += ["--urgency"]
                cmd += [str(urgency)]

            if timeout:
                cmd += ["--timeout"]
                cmd += [str(timeout)]

            if recurrence:
                cmd += ["--recurrence"]
                cmd += [str(recurrence)]

            ret = subprocess.call(cmd)
            return int(ret)
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
