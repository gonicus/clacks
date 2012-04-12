# -*- coding: utf-8 -*-
from clacks.common import Environment
from clacks.agent.objects.filter import ElementFilter
from clacks.common.components import PluginRegistry


class GenerateSambaSid(ElementFilter):
    """
    Out filter to generate a new sambaSID
    """

    def __init__(self, obj):
        super(GenerateSambaSid, self).__init__(obj)
        self.env = Environment.getInstance()

    def process(self, obj, key, valDict, method, number, domain, group_type = 0):
        index = PluginRegistry.getInstance("ObjectIndex")

        #TODO: escape domain
        sid = index.xquery("collection('objects')/o:SambaDomain[lower-case(*/o:sambaDomainName) = lower-case('%s')]//o:sambaSID/string()" % domain)
        if len(sid) != 1:
            raise Exception("No SID found for domain '%s'" % domain)

        dsid = sid[0]
        #TODO: escape domain
        ridbase = index.xquery("collection('objects')/o:SambaDomain[lower-case(*/o:sambaDomainName) = lower-case('%s')]//o:sambaAlgorithmicRidBase/string()" % domain)
        if ridbase:
            ridbase = int(ridbase[0])
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
