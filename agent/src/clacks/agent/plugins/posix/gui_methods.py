# -*- coding: utf-8 -*-
from clacks.common.components import Command
from clacks.common.components import Plugin
from clacks.common.utils import N_
from clacks.common import Environment
from clacks.common.components import PluginRegistry


class GuiMethods(Plugin):
    _target_ = 'misc'

    @Command(__help__=N_("Resolves object information"))
    def getObjectDetails(self, cn, attributes):
        """
        """
        index = PluginRegistry.getInstance("ObjectIndex")
        print index.xquery_dict("collection('objects')/o:PosixGroup/o:Attributes[o:cn='%s']" % (cn))

        return None


