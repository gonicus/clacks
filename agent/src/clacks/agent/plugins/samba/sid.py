# -*- coding: utf-8 -*-
import re
import gettext
from pkg_resources import resource_filename #@UnresolvedImport
from clacks.common import Environment
from clacks.agent.objects.filter import ElementFilter
from clacks.common.components import PluginRegistry
from clacks.agent.objects.comparator import ElementComparator

# Include locales
t = gettext.translation('messages', resource_filename("clacks.agent", "locale"), fallback=True)
_ = t.ugettext

class CheckSambaSIDList(ElementComparator):
    """
    Checks whether the given sambaSIDList can be saved or if it
    will produce recursions.
    """
    def __init__(self, obj):
        super(CheckSambaSIDList, self).__init__()

    def process(self, all_props, key, value):
        errors = []
        if "sambaSID" in all_props and len(all_props["sambaSID"]["value"]):
            sid = all_props["sambaSID"]["value"][0]
            if sid in value:
                errors.append(_("Cannot use ourselves as member for the SID list!"))

        return len(errors)==0, errors

class DetectSambaDomainFromSID(ElementFilter):
    """
    Detects the sambaDomainName for the given SID
    """

    def __init__(self, obj):
        super(DetectSambaDomainFromSID, self).__init__(obj)
        self.env = Environment.getInstance()

    def process(self, obj, key, valDict, sid):

        index = PluginRegistry.getInstance("ObjectIndex")
        sids = index.raw_search({'_type': 'SambaDomain'}, {'sambaSID': 1, 'sambaDomainName': 1})
        for item in sids:
            if re.match("^" + re.escape(item['sambaSID'][0]) + "\-[0-9]*$", sid):
                valDict[key]['value'] = [item['sambaDomainName'][0]]
                return key, valDict

        return key, valDict

class GenerateSambaSid(ElementFilter):
    """
    Out filter to generate a new sambaSID
    """

    def __init__(self, obj):
        super(GenerateSambaSid, self).__init__(obj)
        self.env = Environment.getInstance()

    def process(self, obj, key, valDict, method, number, domain, group_type=0):

        if number == "None":
            raise Exception("No gidNumber available")

        if domain == "None":
            raise Exception("No sambaDomainName available")

        index = PluginRegistry.getInstance("ObjectIndex")
        sid = index.raw_search({'_type': 'SambaDomain', 'sambaDomainName': domain},
            {'sambaSID': 1, 'sambaAlgorithmicRidBase': 1})

        if sid.count() != 1:
            raise Exception("No SID found for domain '%s'" % domain)
        dsid = sid[0]['sambaSID'][0]

        if 'sambaAlgorithmicRidBase' in sid[0]:
            ridbase = int(sid[0]['sambaAlgorithmicRidBase'][0])
        else:
            ridbase = int(self.env.config.get('samba.ridbase', default=1000))

        # Generate a sid for groups or users.
        group_type = int(group_type)
        number = int(number)

        if "group" == method:
            if group_type == 0:
                sid = dsid + "-" + str(number * 2 + ridbase + 1)
            else:
                sid = dsid + "-" + str(group_type)
            valDict[key]['value'] = [sid]

        elif "user" == method:
            sid = dsid + "-" + str(number * 2 + ridbase)
            valDict[key]['value'] = [sid]

        else:
            raise Exception("Unknown method (%s) to generate samba SID!" % method)

        return key, valDict
