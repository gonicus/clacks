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

from zope.interface import Interface, implements


class IResume(Interface):

    def __init__(self):
        pass


class Resume(object):
    implements(IResume)

    def __init__(self):
        pass
