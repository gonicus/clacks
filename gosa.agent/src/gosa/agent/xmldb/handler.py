# -*- coding: utf-8 -*-
import pkg_resources
from gosa.common import Environment


class XMLDBHandler(object):

    instance = None
    __driver = None

    def __init__(self):
        env = Environment.getInstance()
        driver = env.config.get("core.xml-driver", default="DBXml")

        # Find driver module from setuptools advertisement
        for entry in pkg_resources.iter_entry_points("xmldb"):
            mod = entry.load()
            if mod.__name__ == driver:
                self.__driver = mod()
                break

        if not self.__driver:
            raise ValueError("there is no xmldb driver '%s' available" % driver)

    def __getattr__(self, name):
        return getattr(self.__driver, name)

    @staticmethod
    def get_instance():
        if not XMLDBHandler.instance:
            XMLDBHandler.instance = XMLDBHandler()

        return XMLDBHandler.instance
