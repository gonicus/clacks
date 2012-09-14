# -*- coding: utf-8 -*-
from clacks.common.components import Command
from clacks.common.components import Plugin
from clacks.common.utils import N_
from clacks.common.components import PluginRegistry


class SambaGuiMethods(Plugin):
    _target_ = 'misc'

    @Command(__help__=N_("Returns a list with all selectable samba-domain-names"))
    def getSambaDomainNames(self):
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.raw_search({'_type': 'SambaDomain', 'sambaDomainName': {'$exists': True}},
            {'sambaDomainName': 1})

        return list(set([x['sambaDomainName'][0] for x in res]))

    @Command(__help__=N_("Returns a list of DOS/Windows drive letters"))
    def getSambaDriveLetters(self):
        return ["%s:" % c for c in self.letterizer('C', 'Z')]

    def letterizer(self, start='A', stop='Z'):
        for number in xrange(ord(start), ord(stop) + 1):
            yield chr(number)
