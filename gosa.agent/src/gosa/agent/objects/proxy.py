# -*- coding: utf-8 -*-
from logging import getLogger
from gosa.common import Environment
from gosa.agent.objects import GOsaObjectFactory


class GOsaObjectProxy(object):
    __env = None
    __log = None
    __base = None
    __extensions = {}
    __factory = None

    def __init__(self, dn):
        self.__env = Environment.getInstance()
        self.__log = getLogger(__name__)
        self.__factory = GOsaObjectFactory()

        base, extensions = self.__factory.identifyObject(dn)
        all_extensions = self.__factory.getObjectTypes()[base]['extended_by']

        print "-"*80
        print "Base type:", base
        print "Installed extensions:", extensions
        print "Available extensions:", all_extensions
        print "-"*80

    def __getattr__(self, name):
        return name

    def __setattr__(self, name, value):

        # Store non property values
        try:
            object.__getattribute__(self, name)
            self.__dict__[name] = value
            return
        except AttributeError:
            pass

        # Else: lets play
        print "%s = %s" % (name, value)
