# -*- coding: utf-8 -*-
import re
from clacks.agent.objects.filter import ElementFilter


class DetectPasswordMethod(ElementFilter):
    """
    Detects the used password method of a given passwordHash
    """
    def __init__(self, obj):
        super(DetectPasswordMethod, self).__init__(obj)

    def process(self, obj, key, valDict, pwdhash):
        if re.match(r'^{[^\}]+}', pwdhash):
            valDict[key]['value'] = [str(re.sub(r'^{([^\}]+)}.*$','\\1', pwdhash))]
        return key, valDict
