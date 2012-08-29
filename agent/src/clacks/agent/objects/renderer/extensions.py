# -*- coding: utf-8 -*-
from clacks.agent.objects.renderer import ResultRenderer


class ExtensionRenderer(ResultRenderer):

    @staticmethod
    def getName():
        return "extensions"

    @staticmethod
    def render(data):
        if "Extension" in data:
            return "Extensions: " + (", ".join(["<a href='clacks://%s/%s?edit'>%s</a>" % (data['DN'][0], i, i) for i in data['Extension']]))

        return ""
