# -*- coding: utf-8 -*-
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

from unidecode import unidecode #@UnresolvedImport
from clacks.common.components import Command
from clacks.common.components import Plugin
from clacks.common.utils import N_


class Transliterate(Plugin):
    _target_ = 'misc'

    @Command(__help__=N_("Transliterate a given string"))
    def transliterate(self, string):
        """
        Deliver a plain ASCII value of the given string by
        additionally replacing a couple of known characters
        by their ASCII versions.

        ========= =========================
        Parameter Description
        ========= =========================
        string    String to be ASCIIfied
        ========= =========================

        ``Return:`` ASCII string
        """
        table = {
            ord(u'ä'): u'ae',
            ord(u'ö'): u'oe',
            ord(u'ü'): u'ue',
            ord(u'Ä'): u'Ae',
            ord(u'Ö'): u'Oe',
            ord(u'Ü'): u'Ue',
            }
        string = string.translate(table)
        return unidecode(string)
