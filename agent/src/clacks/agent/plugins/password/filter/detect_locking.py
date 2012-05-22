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

    def process(self, obj, key, valDict, pwdhash):
        valDict[key]['value'] = [re.match(r'^{[^\}]+}!', pwdhash) != None]
        return key, valDict
