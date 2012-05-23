# -*- coding: utf-8 -*-
import re
from clacks.agent.objects.filter import ElementFilter


class DetectAccountLockStatus(ElementFilter):
    """
    Detects locking status of an account. By checking the incoming password
    hash for the deactivation flag '!'.
    """
    def __init__(self, obj):
        super(DetectAccountLockStatus, self).__init__(obj)

    def process(self, obj, key, valDict):
        if len(valDict['userPassword']['in_value']):
            pwdh = valDict['userPassword']['in_value'][0]
            valDict[key]['value'] = [re.match(r'^{[^\}]+}!', pwdh) != None]
        return key, valDict
