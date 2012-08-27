# -*- coding: utf-8 -*-
from clacks.agent.objects.filter import ElementFilter
from clacks.agent.objects.backend.registry import ObjectBackendRegistry


class LoadGecosState(ElementFilter):
    """
    Detects the state of the autoGECOS attribute
    """
    def __init__(self, obj):
        super(LoadGecosState, self).__init__(obj)

    def process(self, obj, key, valDict):

        # Only generate gecos if the the autoGECOS field is True.
        if len(valDict["gecos"]['in_value']) and (valDict["gecos"]['in_value'][0]):
             valDict["gecos"]['in_value'][0]


        sn = ""
        givenName = ""
        ou = ""
        telephoneNumber = ""
        homePhone = ""

        if len(valDict["sn"]['in_value']) and (valDict["sn"]['in_value'][0]):
            sn = valDict["sn"]['in_value'][0]
        if len(valDict["givenName"]['in_value']) and (valDict["givenName"]['in_value'][0]):
            givenName = valDict["givenName"]['in_value'][0]
        if len(valDict["homePhone"]['in_value']) and (valDict["homePhone"]['in_value'][0]):
            homePhone = valDict["homePhone"]['in_value'][0]
        if len(valDict["telephoneNumber"]['in_value']) and (valDict["telephoneNumber"]['in_value'][0]):
            telephoneNumber = valDict["telephoneNumber"]['in_value'][0]
        if len(valDict["ou"]['in_value']) and (valDict["ou"]['in_value'][0]):
            ou = valDict["ou"]['in_value'][0]
        print ">>>",sn, givenName, ou, telephoneNumber, homePhone

        return key, valDict


class GenerateGecos(ElementFilter):
    """
    An object filter which automatically generates the posix-gecos
    entry.
    """
    def __init__(self, obj):
        super(GenerateGecos, self).__init__(obj)

    def process(self, obj, key, valDict):

        # Only generate gecos if the the autoGECOS field is True.
        if len(valDict[key]['value']) and (valDict[key]['value'][0]):

            sn = ""
            givenName = ""
            ou = ""
            telephoneNumber = ""
            homePhone = ""

            if len(valDict["sn"]['value']) and (valDict["sn"]['value'][0]):
                sn = valDict["sn"]['value'][0]
            if len(valDict["givenName"]['value']) and (valDict["givenName"]['value'][0]):
                givenName = valDict["givenName"]['value'][0]
            if len(valDict["homePhone"]['value']) and (valDict["homePhone"]['value'][0]):
                homePhone = valDict["homePhone"]['value'][0]
            if len(valDict["telephoneNumber"]['value']) and (valDict["telephoneNumber"]['value'][0]):
                telephoneNumber = valDict["telephoneNumber"]['value'][0]
            if len(valDict["ou"]['value']) and (valDict["ou"]['value'][0]):
                ou = valDict["ou"]['value'][0]

            gecos = "%s %s,%s,%s,%s" % (sn, givenName, ou, telephoneNumber, homePhone)
            valDict["gecos"]['value'] = [gecos]

        return key, valDict

class GetNextID(ElementFilter):
    """
    An object filter which inserts the next free ID for the property
    given as parameter. But only if the current value is empty.

    =============== =======================
    Name            Description
    =============== =======================
    attributeName   The target attribute we want to generate an ID for. uidNumber/gidNumber
    maxValue        The maximum value that would be dsitributed.
    =============== =======================
    """
    def __init__(self, obj):
        super(GetNextID, self).__init__(obj)

    def process(self, obj, key, valDict, attributeName="uidNumber", maxValue=65500):
        if len(valDict[key]['value']) and (valDict[key]['value'][0] == -1):
            maxValue = int(maxValue)

            if len(valDict[key]['backend']) > 1:
                raise Exception("GetNextID filter does not support multiple backends!")

            be = ObjectBackendRegistry.getBackend(valDict[key]['backend'][0])
            gid = be.get_next_id(attributeName)
            if gid > maxValue:
                raise Exception("GID number generation exceeded limitation of %s!" % (maxValue,))
            valDict[key]['value'] = [gid]

        return key, valDict
