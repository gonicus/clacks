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

from lxml.builder import ElementMaker


def EventMaker():
    """
    Returns the even skeleton object which can be directly used for
    extending with event data.
    """
    return ElementMaker(namespace="http://www.gonicus.de/Events", nsmap={None: "http://www.gonicus.de/Events"})
