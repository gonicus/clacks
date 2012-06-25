# -*- coding: utf-8 -*-
from clacks.common.components import PluginRegistry, Plugin
from clacks.common.components.command import Command
from clacks.common.utils import N_
from zope.interface import implements
from clacks.common.handler import IInterfaceHandler


class goFonAccount(Plugin):
    """
    Test
    """
    implements(IInterfaceHandler)

    _priority_ = 99
    _target_ = 'gofon'


    @Command(__help__=N_("Remove the goFon extensions for a given user (uuid)"))
    def removeGoFonAccount(self, uuid):
        print uuid

    @Command(__help__=N_("Adds a goFon extension for a given user (uuid)"))
    def storeGoFonAccount(self, uuid):
        print uuid
