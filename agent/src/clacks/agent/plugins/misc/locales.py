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

import babel
from clacks.common.components import Command
from clacks.common.components import Plugin
from clacks.common.utils import N_


class Locales(Plugin):
    _target_ = 'misc'

    def __init__(self):
        self.__locales = {}

        for lang in babel.Locale("en").languages:
            if "_" in lang:
                continue
            try:
                loc = babel.Locale(lang)
                if loc.display_name:
                    self.__locales[lang] = {'value': "%s (%s)" % (loc.display_name, lang), 'icon': 'flags/%s.png' % lang}
            except babel.core.UnknownLocaleError:
                pass

    @Command(__help__=N_("Return list of languages"))
    def getLanguageList(self, locale=None):
        """
        Deliver a dictionary of language code/display name
        mapping for all supported languages.

        ``Return:`` Dictionary
        """
        return self.__locales
