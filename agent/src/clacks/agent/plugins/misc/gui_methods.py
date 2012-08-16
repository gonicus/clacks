# -*- coding: utf-8 -*-
from clacks.common.components import Command
from clacks.common.components import Plugin
from clacks.common.utils import N_
from clacks.common import Environment
from clacks.common.components import PluginRegistry
from clacks.agent.objects.factory import ObjectFactory
from clacks.agent.objects.backend.back_object_handler import ObjectHandler

class GuiMethods(Plugin):
    _target_ = 'misc'

    @Command(__help__=N_("Resolves object information"))
    def getObjectDetails(self, extension, attribute, names, attributes):
        """
        """
        env = Environment.getInstance()

        # Extract the the required information about the object
        # relation out of the BackendParameters for the given extension.
        of = ObjectFactory.getInstance()
        be_attrs = of.getObjectBackendProperties(extension);
        if not attribute in be_attrs['ObjectHandler']:
            raise Exception("no backend parameter found for %s.%s" % (extension, attribute))

        # Collection basic information
        be_data = ObjectHandler.extractBackAttrs(be_attrs['ObjectHandler'])
        foreignObject, foreignAttr, foreignMatchAttr, matchAttr = be_data[attribute]
        otype = foreignObject
        oattr = foreignAttr
        base = env.base

        # Create list of conditional statements
        l = []
        if not oattr in names:
            names.append(oattr)
        snames = ['"%s"' % n for n in names]
        condition = '(%s.%s = %s)'  % (otype, oattr, "(%s)" % (", ".join(snames)))

        # Create a list of attributes that will be requested
        a = []
        for attr in attributes:
            a.append("%s.%s" % (otype, attr))
        attrs = ", ".join(a)

        # Prepare the query
        query = """
            SELECT %(attrs)s
            BASE %(type)s SUB "%(base)s"
            WHERE %(condition)s
            """ % {"attrs": attrs, "condition": condition, "type": otype, "base": base}

        # Start the query and brind the result in a usable form
        search = PluginRegistry.getInstance("SearchWrapper")
        res =  search.execute(query)
        result = {}
        mapping = {}

        for entry in names:
            id = len(result)
            mapping[entry] = id
            result[id] = None

        for entry in res:
            item = {}
            for attr in attributes:
                if attr in entry[otype] and len(entry[otype][attr]):
                    item[attr] = entry[otype][attr][0]
                else:
                    item[attr] = ""

            id = mapping[item[oattr]]
            result[id] = item
        return {"result": result, "map": mapping}


