# -*- coding: utf-8 -*-
from clacks.common.components import Command
from clacks.common.components import Plugin
from clacks.common.utils import N_
from clacks.common import Environment
from clacks.common.components import PluginRegistry


class GuiMethods(Plugin):
    _target_ = 'misc'

    @Command(__help__=N_("Resolves object information"))
    def getObjectDetails(self, names, attributes):
        """
        """

        otype = "PosixGroup"
        oattr = "cn"
        base = "dc=example,dc=net"

        l = []
        for item in names:
            l.append('(%s.%s = "%s")' % (otype, oattr, item))

        a = []
        for attr in attributes:
            a.append("%s.%s" % (otype, attr))

        attrs = ", ".join(a)
        condition = " OR ".join(l)


        query = """
            SELECT %(attrs)s
            BASE %(type)s SUB "%(base)s"
            WHERE %(condition)s
            """ % {"attrs": attrs, "condition": condition, "type": otype, "base": base}

        search = PluginRegistry.getInstance("SearchWrapper")
        res =  search.execute(query)
        result = []
        for entry in res:
            item = {}
            for attr in attributes:
                if attr in entry[otype] and len(entry[otype][attr]):
                    item[attr] = entry[otype][attr][0]
                else:
                    item[attr] = ""
            result.append(item)
        return result


