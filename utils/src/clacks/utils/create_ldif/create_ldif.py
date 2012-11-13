#!/usr/bin/env python
import argparse
import os
import re
import sys

class NoSuchTemplateException(Exception):
    pass


class Line(object):

    generator = None
    attrName = None
    elements = None

    def __init__(self, generator, attrName, elements):

        self.generator = generator
        self.attrName = attrName
        self.elements = elements

    def __repr__(self):
        return self.attrName + ": ..."

    def process(self):
        result = ""
        for item in self.elements:
            if type(item) == str:
                result = result + item
            else:
                result = result + item.process()

        return result


class getFunction(object):

    name = None
    generator= None
    params = None

    def __init__(self, generator, parts):

        name = re.sub("^([^(]*).*$", "\\1", "".join([f for f in parts[1:-1] if type(f) in [str]]))
        tmp_params = parts[len(name)+2:-2]
        params = {}

        param_id = 0
        params[param_id] = []
        for item in tmp_params:
            if item == ",":
                param_id = param_id + 1 
                params[param_id] = []
                continue

            params[param_id].append(item)

        self.params = params.values()
        self.name = name
        self.generator = generator

    def __repr__(self):
        return self.name + "(...)"

    def process(self):

        func = getattr(self.generator, self.name)
        params = []
        for para in self.params:
            str_para = ""
            for item in para:
                if type(item) == str:
                    str_para = str_para + item
                else:
                    str_para = str_para + item.process()

            params.append(str_para)
        return func(params)


class getAttr(object):

    name = None
    generator= None

    def __init__(self, generator, name):
        self.name = name
        self.generator = generator

    def __repr__(self):
        return "["+self.name+"]"

    def process(self):
        return self.name

class LdifGenerator(object):

    _use = {}
    _templates = {}
    _templatePath = None

    def generate_unique_dn(self, args):
        return "called"

    def generate_unique_uid(self, args):
        return "called"

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
        for root, subFolders, files in os.walk(self._templatePath):
            for file in files:
                path = os.path.join(root, file)
                self._templates[os.path.splitext(file)[0]] = self._processTemplate(open(path).read());

    def _processTemplate(self, content):

        lines = content.split("\n")
        objectList = []
        regex = "(^.*(%([a-zA-Z_][a-zA-Z0-9_-]*)?\([^\)\(]*\)[fs]).*)$"
        for line in lines:

            attrName = re.sub("^([^=]*)=.*$", "\\1" , line)
            line = re.sub("^[^=]*=(.*)$", "\\1" , line)
            match = re.match(regex, line)

            lineList = list(line)

            while match:
                line = match.group(0)
                matched = match.group(2)
                start = match.start(2)
                end = match.end(2)

                # Replace item with a string
                if matched[-1] == "s":
                    replacement = getAttr(self, matched[2:-2])

                if matched[-1] == "f":
                    replacement = getFunction(self, lineList[start:end])

                line = line[0:start] + "!" +line[end:]
                lineList = lineList[0:start] + [replacement] + lineList[end:]
                match = re.match(regex, line)

            line_object = Line(self, attrName, lineList)
            objectList.append(line_object)
        return(objectList)


    def generate(self):

        for template in self._templates:

            print "##" + template+ "##"
            for line in self._templates[template]:
                print line.process()


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
