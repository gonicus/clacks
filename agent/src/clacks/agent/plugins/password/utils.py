# -*- coding: utf-8 -*-
from clacks.common.components import Command
from clacks.common.components import Plugin
from clacks.common.utils import N_
from clacks.common import Environment
from clacks.agent.objects.factory import STATUS_CHANGED, STATUS_OK
from clacks.agent.objects.filter import ElementFilter
from clacks.agent.objects.types import AttributeType
from clacks.agent.objects.backend.registry import ObjectBackendRegistry

import re

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


class DetectAccountLockStatus(ElementFilter):
    """
    Detects locking status of an account. By checking the incoming password hash for the deactivation flag '!'.
    """
    def __init__(self, obj):
        super(DetectAccountLockStatus, self).__init__(obj)

    def process(self, obj, key, valDict, pwdhash):
        valDict[key]['value'] = [re.match(r'^{[^\}]+}!', pwdhash) != None]
        return key, valDict


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
