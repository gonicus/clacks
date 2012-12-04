# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

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
