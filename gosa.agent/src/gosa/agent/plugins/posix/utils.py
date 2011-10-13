# -*- coding: utf-8 -*-
from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.utils import N_
from gosa.common import Environment
from gosa.agent.objects.filter import ElementFilter
from gosa.agent.objects.types import AttributeType
from gosa.agent.objects.backend.registry import ObjectBackendRegistry


class GetNextID(ElementFilter):
    """
    An object filter which inserts the next free ID for the property given as parameter.
    But only if the current value is empty.
    """
    def __init__(self, obj):
        super(GetNextID, self).__init__(obj)

    def process(self, obj, key, valDict, attributeName="uidNumber"):
        if len(valDict[key]['value']) and (valDict[key]['value'][0] == -1):
            be = ObjectBackendRegistry.getBackend(valDict[key]['backend'])
            valDict[key]['value'] = [be.get_next_id(attributeName)]

        return key, valDict
