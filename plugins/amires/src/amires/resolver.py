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
from clacks.common import Environment


class PhoneNumberResolver(object):
    """
    TODO

    Configuration keys for section **resolver-replace**

    +------------------+------------+-------------------------------------------------------------+
    + Key              | Format     +  Description                                                |
    +==================+============+=============================================================+
    +                  |            +                                                             |
    +------------------+------------+-------------------------------------------------------------+

    """
    priority = 10
    replace = []

    def __init__(self):
        self.env = env = Environment.getInstance()

        # read replacement configuration
        if not PhoneNumberResolver.replace:
            for opt in env.config.getOptions("resolver-replace"):
                itm = env.config.get("resolver-replace.%s" % opt)
                res = re.search("^\"(.*)\",\"(.*)\"$", itm)
                res = re.search("^\"(.*)\"[\s]*,[\s]*\"(.*)\"$", itm)

                if res:
                    PhoneNumberResolver.replace.append([res.group(1), res.group(2)])

    def replaceNumber(self, number):
        # Apply configured substitutions on number
        for rep in PhoneNumberResolver.replace:
            number = re.sub(rep[0], rep[1], number)

        return number

    def resolve(self):
        raise NotImplementedError("resolve is not implemented")
