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

import os
import unittest
from clacks.common import Environment
from clacks.agent.plugins.goto.network import NetworkUtils

Environment.reset()
Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test.conf")
Environment.noargs = True


class TestGOtoPlugin(unittest.TestCase):

    def test_mksmbhash(self):
        #TODO: mockup env
        network = NetworkUtils() #@UnusedVariable
        #networkCompletion
        #getMacManufacturer
        #self.assertEqual(sambaUtils.mksmbhash('secret'), '552902031BEDE9EFAAD3B435B51404EE:878D8014606CDA29677A44EFA1353FC7')
        #self.assertEqual(sambaUtils.mksmbhash(''), 'AAD3B435B51404EEAAD3B435B51404EE:31D6CFE0D16AE931B73C59D7E0C089C0')
        #self.assertRaises(TypeError, sambaUtils.mksmbhash, None, '')

if __name__ == "__main__":
    unittest.main()
