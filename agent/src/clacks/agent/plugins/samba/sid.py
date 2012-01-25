# -*- coding: utf-8 -*-
from clacks.agent.objects.filter import ElementFilter


class GenerateSambaSid(ElementFilter):
    """
    Out filter to generate a new sambaSID
    """

    def __init__(self, obj):
        super(GenerateSambaSid, self).__init__(obj)

    def process(self, obj, key, valDict, method, number, domain, group_type = 0):

        #TODO: Get this information from the backend/config
        ridbase = 1000

        #TODO: Get this information from the domain object
        dsid = "S-1-5-21-328194278-237061239-1145748033"

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
