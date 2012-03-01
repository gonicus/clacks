# -*- coding: utf-8 -*-
from zope.interface import Interface, implements


class IResume(Interface):

    def __init__(self):
        pass


class Resume(object):
    implements(IResume)

    def __init__(self):
        pass
