# -*- coding: utf-8 -*-
from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.utils import N_
from gosa.common import Environment
from gosa.agent.objects.filter import ElementFilter
from gosa.agent.objects.types import AttributeType
from gosa.agent.objects.backend.registry import ObjectBackendRegistry

class PosixUtils(Plugin):
    """
    Utility class that contains methods needed to handle posix
    functionality.
    """
    _target_ = 'posix'

    def __init__(self):
        env = Environment.getInstance()
        self.env = env

    @Command(__help__=N_("Find the next free id for the given attribute."))
    def get_next_id(self, attribute="uidNumber"):
        """
        Returns the next free id for the given attribute!

        ========== ============
        Parameter  Description
        ========== ============
        attribute  The name of the attribute want to get the next free id for. (default is 'uidNumber')
        ========== ============

        ``Return:`` An integer value representing the next free id.
        """
        return(ObjectBackendRegistry.getBackend(valDict[key]['backend']).get_next_id(attribute))


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
