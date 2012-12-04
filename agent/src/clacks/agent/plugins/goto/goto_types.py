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

from clacks.agent.objects.types import AttributeType
from clacks.common.components import PluginRegistry


class DevicePartitionTableType(AttributeType):
    """
    A special attribute-type-definition used by the InstalledDevice object-extension.
    It converts a partition definition from string into a json-object representation that
    can then be passed through the json proxy to the user.
    """

    __alias__ = "DevicePartitionTableType"

    def values_match(self, value1, value2):
        return str(value1) == str(value2)

    def is_valid_value(self, value):
        for item in value:
            if type(item) != dict or '__jsonclass__' not in item:
                return False
        return True

    def _convert_to_unicodestring(self, value):
        rom = PluginRegistry.getInstance('JSONRPCObjectMapper')
        cr = PluginRegistry.getInstance('CommandRegistry')
        new_value = []
        for item in value:
            uuid = item['__jsonclass__'][1][1]
            new_value.append(rom.dispatchObjectMethod(uuid, 'dump'))
            cr.call('closeObject', uuid)
        return new_value

    def _convert_from_string(self, value):
        return self._convert_from_unicodestring(value)

    def _convert_from_unicodestring(self, value):
        cr = PluginRegistry.getInstance('CommandRegistry')
        new_values = []
        for item in value:
            new_values.append(cr.call('openObject', 'libinst.diskdefinition', definition=item))
        return new_values
