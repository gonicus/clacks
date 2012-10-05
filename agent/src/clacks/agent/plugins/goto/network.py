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

import socket
import dumbnet #@UnresolvedImport
from netaddr import EUI, NotRegisteredError
from telnetlib import Telnet

from clacks.common.components import Plugin
from clacks.common.utils import N_
from clacks.common.components.command import Command, FIRSTRESULT


class NetworkUtils(Plugin):
    """
    Module containing network utilities like DNS/MAC resolving and
    manufacturer resolving.
    """
    _target_ = 'goto'
    oui = None

    @Command(type=FIRSTRESULT, __help__=N_("Resolve network address to a mac / dns name tupel."))
    def networkCompletion(self, name):
        """
        TODO
        """
        protocolAddress = socket.gethostbyname(name)
        networkAddress = self.getMacFromIP(protocolAddress)
        return {'ip': protocolAddress, 'mac': networkAddress}

    def __sendPacket(self, protocolAddress):
        try:
            tn = Telnet(protocolAddress, 139, 1)
            tn.close()
        except Exception:
            pass

    def getMacFromARP(self, protocolAddress):
        arp = dumbnet.arp()
        return arp.get(dumbnet.addr(protocolAddress))

    def getMacFromIP(self, protocolAddress):
        result = self.getMacFromARP(protocolAddress)
        if not result:
            self.__sendPacket(protocolAddress)
            result = self.getMacFromARP(protocolAddress)
        return str(result)

    @Command(__help__=N_("Resolve MAC address to the producer of the network card if possible."))
    def getMacManufacturer(self, mac):
        """
        This function uses the ieee file provided at
        http://standards.ieee.org/regauth/oui/oui.txt

        TODO
        """
        try:
            mac = EUI(mac)
            oui = mac.oui.registration()
        except NotRegisteredError:
            return None
        # pylint: disable=E1101
        return oui.org
