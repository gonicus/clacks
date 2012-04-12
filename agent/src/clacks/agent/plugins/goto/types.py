# -*- coding: utf-8 -*-
from clacks.agent.objects.types import AttributeType
from clacks.common.components import PluginRegistry, ObjectRegistry


class DevicePartitionTableType(AttributeType):
    """
    TODO
    """

    __alias__ = "DevicePartitionTableType"

    def values_match(self, value1, value2):
        #TODO
        return(str(value1) == str(value2))

    def is_valid_value(self, value):
        #TODO
        return False

    def _convert_to_unicodestring(self, value):
        #TODO
        return(value)

    def _convert_from_string(self, value):
        #TODO
        return self._convert_from_unicodestring(value)

    def _convert_from_unicodestring(self, value):
        cr = PluginRegistry.getInstance('CommandRegistry')
        new_values = []
        for item in value:
            new_values.append(cr.call('openObject', 'libinst.diskdefinition', definition=item))
        return(new_values)
