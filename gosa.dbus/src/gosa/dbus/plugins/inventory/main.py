#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dbus.service
from gosa.common import Environment
from gosa.common.components import Plugin
from gosa.dbus import get_system_bus


class DBusInventoryHandler(dbus.service.Object, Plugin):
    """ This handler collect client inventory data """

    def __init__(self):
        conn = get_system_bus()
        dbus.service.Object.__init__(self, conn, '/com/gonicus/gosa/inventory')
        self.env = Environment.getInstance()

    @dbus.service.method('com.gonicus.gosa', in_signature='', out_signature='s')
    def inventory():
        return "Ja"
