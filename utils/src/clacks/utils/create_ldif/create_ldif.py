#!/usr/bin/env python
import argparse
import os
import sys

class NoSuchTemplateException(Exception):
    pass

class LdifGenerator(object):

    _use = {}
    _templates = {}
    _templatePath = None

    def __init__(self, templatePath):
        self._templatePath = templatePath
        self._loadTemplates();

    def use(self, o_type, amount):
        """
        Tell the generator to use the given type of object while generating
        the ldif.
        """
        if o_type not in self._templates:
            raise NoSuchTemplateException("missing template for '%s'!" % (o_type))
        self._use[o_type] = amount

    def _loadTemplates(self):
        """
        Loads all templates, from the given tempalte path.
        The templates will be stored in self._templates.
        """
        fileList = []
        rootdir = sys.argv[1]
        for root, subFolders, files in os.walk(self._templatePath):
            for file in files:
                path = os.path.join(root, file)
                self._templates[os.path.splitext(file)[0]] = open(path).read();

    def _processTemplate(self, o_type):

        lines = self._templates[o_type].split("\n")
        for line in lines:
            print line


    def generate(self):

        for item in self._use:
            amount = self._use[item]

            for i in range(amount):
                self._processTemplate(item)


def main():
    p = argparse.ArgumentParser(description="This program generates a ldif containing the given set of objects (user, groups, ...) that can easily imported into your ldap server for demo purpose.")

    p.add_argument('-t', '--templatePath', dest="templatePath", default="templates")
    p.add_argument('-u', '--user', dest="useUsers", default=False, action='store_true')
    p.add_argument('-g', '--groups', dest="useGroups", default=False, action='store_true')
    p.add_argument('-U', '--number-users', dest="numberUsers", default=100, type=int)
    p.add_argument('-G', '--number-groups', dest="numberGroups", default=100, type=int)
    args = p.parse_args()

    generator = LdifGenerator(args.templatePath)
    if args.useUsers:
        generator.use("user", args.numberUsers)

    if args.useGroups:
        generator.use("group", args.numberGroups)

    generator.generate()

if __name__ == '__main__':
    main()
