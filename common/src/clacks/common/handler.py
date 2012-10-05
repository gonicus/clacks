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

"""
The usage of the zope interface is in progress. Currently, it is just used as a
marker.
"""
import zope.interface


class IInterfaceHandler(zope.interface.Interface):
    """ Mark a plugin to be the manager for a special interface """
    pass


class IPluginHandler(zope.interface.Interface):
    """ Mark a plugin to be the manager for a special interface """
    pass
