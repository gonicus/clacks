# -*- coding: utf-8 -*-
__import__('pkg_resources').declare_namespace(__name__)
import pkg_resources


def get_renderers():
    res = {}
    for entry in pkg_resources.iter_entry_points("object.renderer"):
        module = entry.load()
        res[module.getName()] = module.render

    return res


class ResultRenderer(object):

    @staticmethod
    def getName():
        raise NotImplementedError("not implemented")

    @staticmethod
    def render(value):
        raise NotImplementedError("not implemented")
