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
        """
        Detects whether this password hash was marked as locked or not
        """
        if len(valDict['userPassword']['in_value']):
            pwdh = valDict['userPassword']['in_value'][0]
            valDict[key]['value'] = [re.match(r'^{[^\}]+}!', pwdh) is not None]
        return key, valDict
