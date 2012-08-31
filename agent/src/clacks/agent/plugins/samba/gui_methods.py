# -*- coding: utf-8 -*-
from clacks.common.components import Command
from clacks.common.components import Plugin
from clacks.common.utils import N_


class SambaGuiMethods(Plugin):
    _target_ = 'misc'

    @Command(__help__=N_("Returns a list of all selectable samba domain names"))
    def getSambaDomainNames(self):
        return ["a", "b"]
