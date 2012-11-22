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
    This is the mainclass for any PhoneNumberResolver module. PhoneNumberResolver
    modules try to retrieve basic information about a phone number (such as the
    callers name or company) from a certain information source they are dedicated
    to (e.g. a phonebook database or LDAP directory). Some of this information
    will be printet by the common renderer module (common_render.py) or can be
    used for retrieving more detailed information by some dedicated renderer module.

    The configuration happens to be in the **resolver-replace** section of your
    configuration files and is dynamic:

    Any key-value pair in this section manipulates the original phone number by
    applying a substitution on it (see :ref:`python:re.sub`). This is neccessary
    in order to bring a phone number from a format that is location specific
    (e.g. an internal company number) into a format that is understood by the
    resolver module (usually the international number format: *+490123456789*).

    The key-value paires in this section are applied in top to buttom order -
    the key has just a label function in this case.
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
