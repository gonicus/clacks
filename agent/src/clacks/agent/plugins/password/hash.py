# -*- coding: utf-8 -*-
import re
from clacks.agent.objects.factory import STATUS_OK
from clacks.agent.objects.filter import ElementFilter


class GeneratePasswordHash(ElementFilter):
    """
    Generates a new password hash.
    """
    def __init__(self, obj):
        super(GeneratePasswordHash, self).__init__(obj)

    def process(self, obj, key, valDict, method, is_locked):

        is_locked = is_locked == "True"

        # Get current pwdhash
        pwdhash = ""
        if valDict[key]['value']:
            pwdhash = valDict[key]['value'][0]

        # Generate new pwd hash
        if valDict[key]['status'] == STATUS_CHANGED:
            pwdhash = "{%s}213GERSDF2351" % (method,)

        # Unlock account
        if pwdhash:
            if re.match(r'^{[^\}]+}!', pwdhash) and not is_locked:
                pwdhash = re.sub(r'^({[^\}]+})!(.*)$',"\\1\\2", pwdhash)
            elif not re.match(r'^{[^\}]+}!', pwdhash) and is_locked:
                pwdhash = re.sub(r'^({[^\}]+})(.*)$',"\\1!\\2", pwdhash)

        valDict[key]['value'] = [pwdhash]
        return key, valDict
