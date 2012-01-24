# -*- coding: utf-8 -*-
from unidecode import unidecode
from clacks.common.components import Command
from clacks.common.components import Plugin
from clacks.common.utils import N_


class Transliterate(Plugin):
    _target_ = 'misc'

    @Command(__help__=N_("Transliterate a given string"))
    def transliterate(self, string):
        """
        Deliver a plain ASCII value of the given string by
        additionaly replacing a couple of known characters
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
