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

from clacks.common.components import Command
from clacks.common.components import Plugin
from clacks.common.utils import N_
from clacks.common import Environment


class ShellSupport(Plugin):
    _target_ = 'misc'

    def __init__(self):
        self.__shells = {}

        # Use a shell source file
        env = Environment.getInstance()
        source = env.config.get('goto.shells', default="/etc/shells")

        with open(source) as f:
            self.__shells = filter(lambda y: not y.startswith("#"), [x.strip() for x in f.read().split("\n")])

    @Command(__help__=N_("Return list of supported shells"))
    def getShellList(self):
        """
        Deliver a list of supported shells.

        ``Return:`` List
        """
        return self.__shells
