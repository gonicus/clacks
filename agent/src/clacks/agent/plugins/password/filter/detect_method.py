# -*- coding: utf-8 -*-
from clacks.agent.objects.filter import ElementFilter
from clacks.agent.plugins.password.manager import PasswordManager


class DetectPasswordMethod(ElementFilter):
    """
    Detects the used password method of a given passwordHash
    """
    def __init__(self, obj):
        super(DetectPasswordMethod, self).__init__(obj)

    def process(self, obj, key, valDict):
        """
        Detects what password-method was used to generate this hash.
        """

        if len(valDict['userPassword']['in_value']):
            pwdh = valDict['userPassword']['in_value'][0]

            # Get passord manager to identify the responsible password-method
            pwd_m = PasswordManager.get_instance()
            pwd_method = pwd_m.detect_method_by_hash(pwdh)

            # Get the used hashing method
            valDict[key]['value'] = []
            if pwd_method:
                method = pwd_method.detect_hash_method(pwdh)
                if method:
                    valDict[key]['value'] = [method]
        return key, valDict
