# -*- coding: utf-8 -*-
import dbus
from gosa.common.components import Plugin
from gosa.common.components import Command
from gosa.common import Environment

from gosa.client.plugins.inventory.utils import Inventory


a = Inventory()
a.request_inventory()
