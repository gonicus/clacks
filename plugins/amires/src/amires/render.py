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

import cgi


def mr(data):
    try:
        return data.decode("utf-8")
    except:
        try:
            return data.decode("raw_unicode_escape").encode("utf-8")
        except:
            try:
                return data.encode("raw_unicode_escape").decode("utf-8")
            except:
                return data


class BaseRenderer(object):
    """
    TODO
    """
    priority = 1

    def __init__(self):
        pass


    def getHTML(self, particiantInfo, selfInfo, event):
        if not particiantInfo:
            raise RuntimeError("particiantInfo must not be None.")
        if type(particiantInfo) is not dict:
            raise TypeError("particiant Info must be a dictionary.")
