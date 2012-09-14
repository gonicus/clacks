# -*- coding: utf-8 -*-
from clacks.common.components import Command
from clacks.common.components import Plugin
from clacks.common.utils import N_
from clacks.common import Environment
from clacks.common.components import PluginRegistry
from clacks.agent.objects import ObjectProxy
from clacks.agent.objects.factory import ObjectFactory
from clacks.agent.objects.backend.back_object_handler import ObjectHandler
from json import loads, dumps


class GuiMethods(Plugin):
    _target_ = 'misc'

    @Command(__help__=N_("Get all translations bound to templates."))
    def getTemplateI18N(self, language, theme="default"):
        templates = []
        factory = ObjectFactory.getInstance()

        for otype in factory.getObjectTypes():
            templates += factory.getObjectTemplates(otype)

        return factory.getNamedI18N(list(set(templates)), language=language, theme=theme)

    @Command(__help__=N_("Save user preferences"))
    def saveUserPreferences(self, userid, name, value):
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.raw_search({'_type': 'User', 'uid': userid}, {'dn': 1})
        if not res.count():
            raise Exception("No such user %s" % (userid))

        user = ObjectProxy(res[0]['dn'])
        prefs = user.guiPreferences

        if not prefs:
            prefs = {}
        else:
            prefs = loads(prefs)

        prefs[name] = value
        user.guiPreferences = dumps(prefs)
        user.commit()

        return True

    @Command(__help__=N_("Load user preferences"))
    def loadUserPreferences(self, userid, name):
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.raw_search({'_type': 'User', 'uid': userid}, {'dn': 1})
        if not res.count():
            raise Exception("No such user %s" % (userid))

        user = ObjectProxy(res[0]['dn'])
        prefs = user.guiPreferences

        if not prefs:
            prefs = {}
        else:
            prefs = loads(prefs)

        if name in prefs:
            return prefs[name]

        return None

    @Command(__help__=N_("Search for object informations"))
    def searchForObjectDetails(self, extension, attribute, fltr, attributes, skip_values):
        """
        Search selectable items valid for the attribute "extension.attribute".

        This is used to add new groups to the users groupMemeberhip attribute.
        """
        env = Environment.getInstance()

        # Extract the the required information about the object
        # relation out of the BackendParameters for the given extension.
        of = ObjectFactory.getInstance()
        be_attrs = of.getObjectBackendProperties(extension)
        be_data = None
        for be_name in be_attrs:
            if attribute in be_attrs[be_name]:
                be_data = ObjectHandler.extractBackAttrs(be_attrs[be_name])

        if not be_data:
            raise Exception("no backend parameter found for %s.%s" % (extension, attribute))

        # Collection basic information
        foreignObject, foreignAttr, foreignMatchAttr, matchAttr, additionalFilter = be_data[attribute]  #@UnusedVariable
        otype = foreignObject
        oattr = foreignAttr
        base = env.base

        # Create list of conditional statements
        condition = '(%s.%s LIKE "%s")' % (otype, oattr, fltr)

        if additionalFilter:
            additionalFilter = " AND " + additionalFilter

        # Create a list of attributes that will be requested
        a = []
        if oattr not in attributes:
            attributes.append(oattr)
        for attr in attributes:
            a.append("%s.%s" % (otype, attr))
        attrs = ", ".join(a)

        # Prepare the query
        query = """
            SELECT %(attrs)s
            BASE %(type)s SUB "%(base)s"
            WHERE %(condition)s %(filter)s
            """ % {"attrs": attrs, "condition": condition, "type": otype, "base": base, "filter": additionalFilter}

        # Start the query and brind the result in a usable form
        search = PluginRegistry.getInstance("SearchWrapper")
        res = search.execute(query)
        result = []

        for entry in res:
            item = {}
            for attr in attributes:
                if attr in entry[otype] and len(entry[otype][attr]):
                    item[attr] = entry[otype][attr][0]
                else:
                    item[attr] = ""
            item['__identifier__'] = item[foreignAttr]

            # Skip values that are in the skip list
            if skip_values and item['__identifier__'] in skip_values:
                continue

            result.append(item)

        return result

    @Command(__help__=N_("Resolves object information"))
    def getObjectDetails(self, extension, attribute, names, attributes):
        """
        This method is used to complete object information shown in the gui.
        e.g. The groupMembership table just knows the groups cn attribute.
             To be able to show the description too, it uses this method.
        """
        env = Environment.getInstance()

        # Extract the the required information about the object
        # relation out of the BackendParameters for the given extension.
        of = ObjectFactory.getInstance()
        be_attrs = of.getObjectBackendProperties(extension)
        be_data = None
        for be_name in be_attrs:
            if attribute in be_attrs[be_name]:
                be_data = ObjectHandler.extractBackAttrs(be_attrs[be_name])

        if not be_data:
            raise Exception("no backend parameter found for %s.%s" % (extension, attribute))

        # Collection basic information
        foreignObject, foreignAttr, foreignMatchAttr, matchAttr, additionalFilter = be_data[attribute]  #@UnusedVariable
        otype = foreignObject
        oattr = foreignAttr
        base = env.base

        # Create list of conditional statements
        if not oattr in names:
            names.append(oattr)
        snames = ['"%s"' % n for n in names]
        condition = '(%s.%s = %s)' % (otype, oattr, "(%s)" % (", ".join(snames)))

        # Create a list of attributes that will be requested
        a = []
        if oattr not in attributes:
            attributes.append(oattr)
        for attr in attributes:
            a.append("%s.%s" % (otype, attr))
        attrs = ", ".join(a)

        if additionalFilter:
            additionalFilter = " AND " + additionalFilter

        # Prepare the query
        query = """
            SELECT %(attrs)s
            BASE %(type)s SUB "%(base)s"
            WHERE %(condition)s %(filter)s
            """ % {"attrs": attrs, "condition": condition, "type": otype, "base": base, "filter": additionalFilter}

        # Start the query and brind the result in a usable form
        search = PluginRegistry.getInstance("SearchWrapper")
        res = search.execute(query)
        result = {}
        mapping = {}

        for entry in names:
            _id = len(result)
            mapping[entry] = _id
            result[_id] = None

        for entry in res:
            item = {}
            for attr in attributes:
                if attr in entry[otype] and len(entry[otype][attr]):
                    item[attr] = entry[otype][attr][0]
                else:
                    item[attr] = ""

            _id = mapping[item[oattr]]
            result[_id] = item

        return {"result": result, "map": mapping}
