# -*- coding: utf-8 -*-
import re
from clacks.common.components import Command
from clacks.common.components import Plugin
from clacks.common.utils import N_
from clacks.common.components import PluginRegistry
from clacks.agent.objects import ObjectProxy
from clacks.agent.objects.factory import ObjectFactory
from json import loads, dumps


class GuiMethods(Plugin):
    _target_ = 'misc'

    @Command(__help__=N_("Returns a list containing all available object names"))
    def getAvailableObjectNames(self):
        factory = ObjectFactory.getInstance()
        return factory.getAvailableObjectNames()

    @Command(__help__=N_("Returns all templates used by the given object type."))
    def getGuiTemplates(self, objectType, theme="default"):
        factory = ObjectFactory.getInstance()
        if objectType not in factory.getObjectTypes():
            raise Exception("No such object type: %s" % (objectType))

        return factory.getObjectTemplates(objectType, theme)

    @Command(__help__=N_("Get all translations bound to templates."))
    def getTemplateI18N(self, language, theme="default"):
        templates = []
        factory = ObjectFactory.getInstance()

        for otype in factory.getObjectTypes():
            templates += factory.getObjectTemplateNames(otype)

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

    @Command(__help__=N_("Search for object information"))
    def searchForObjectDetails(self, extension, attribute, fltr, attributes, skip_values):
        """
        Search selectable items valid for the attribute "extension.attribute".

        This is used to add new groups to the users groupMembership attribute.
        """

        # Extract the the required information about the object
        # relation out of the BackendParameters for the given extension.
        of = ObjectFactory.getInstance()
        be_data = of.getObjectBackendParameters(extension, attribute)
        if not be_data:
            raise Exception("no backend parameter found for %s.%s" % (extension, attribute))

        # Collection basic information
        otype, oattr, foreignMatchAttr, matchAttr = be_data[attribute] #@UnusedVariable

        # Create a list of attributes that will be requested
        if oattr not in attributes:
            attributes.append(oattr)
        attrs = dict([(x, 1) for x in attributes])

        # Start the query and brind the result in a usable form
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.raw_search({
            '$or': [{'_type': otype}, {'_extensions': otype}],
            oattr: re.compile("^.*" + re.escape(fltr) + ".*$")
            }, attrs)
        result = []

        for entry in res:
            item = {}
            for attr in attributes:
                if attr in entry and len(entry[attr]):
                    item[attr] = entry[attr] if attr == "dn" else entry[attr][0]
                else:
                    item[attr] = ""
            item['__identifier__'] = item[oattr]

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

        #TODO: @fabian - this function is about 95% the same than the one
        #                above.
        """

        # Extract the the required information about the object
        # relation out of the BackendParameters for the given extension.
        of = ObjectFactory.getInstance()
        be_data = of.getObjectBackendParameters(extension, attribute)

        if not be_data:
            raise Exception("no backend parameter found for %s.%s" % (extension, attribute))

        # Collection basic information
        otype, oattr, foreignMatchAttr, matchAttr = be_data[attribute] #@UnusedVariable

        # Create a list of attributes that will be requested
        if oattr not in attributes:
            attributes.append(oattr)
        attrs = dict([(x, 1) for x in attributes])

        # Start the query and brind the result in a usable form
        index = PluginRegistry.getInstance("ObjectIndex")

        res = index.raw_search({
            '$or': [{'_type': otype}, {'_extensions': otype}],
            oattr: {'$in': names}
            }, attrs)

        result = {}
        mapping = {}

        for entry in names:
            _id = len(result)
            mapping[entry] = _id
            result[_id] = None

        for entry in res:
            item = {}
            for attr in attributes:
                if attr in entry and len(entry[attr]):
                    item[attr] = entry[attr] if attr == 'dn' else entry[attr][0]
                else:
                    item[attr] = ""

            _id = mapping[item[oattr]]
            result[_id] = item

        return {"result": result, "map": mapping}

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
