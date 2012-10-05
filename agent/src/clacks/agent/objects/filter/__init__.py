# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

__import__('pkg_resources').declare_namespace(__name__)
import pkg_resources


def get_filter(name):
    for entry in pkg_resources.iter_entry_points("object.filter"):
        module = entry.load()
        if module.__name__ == name:
            return module

    raise KeyError("no filter instance for '%s' found" % name)


class ElementFilter(object):

    def __init__(self, obj):
        pass

    def process(self, obj, key, value):
        raise NotImplementedError("not implemented")

    def __copy__(self):
        """
        Do not make copies of ourselves.
        """
        return self

    def __deepcopy__(self, memo):
        """
        Do not make copies of ourselves.
        """
        return self


class ElementFilterException(Exception):
    pass
