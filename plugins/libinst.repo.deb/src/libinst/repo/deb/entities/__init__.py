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

__import__('pkg_resources').declare_namespace(__name__)
# pylint: disable-msg=E0611
from pkg_resources import resource_filename #@UnresolvedImport
import gettext

# Include locales
t = gettext.translation('messages', resource_filename("libinst.repo.deb", "locale"), fallback=True)
_ = t.ugettext
