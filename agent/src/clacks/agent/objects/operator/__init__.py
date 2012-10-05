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


def get_operator(name):
    for entry in pkg_resources.iter_entry_points("object.operator"):
        module = entry.load()
        if module.__name__ == name:
            return module

    raise KeyError("no operator instance for '%s' found" % name)


class ElementOperator(object):

    def __init(self, obj):
        pass

    def process(self, *args, **kwargs):
        raise NotImplementedError("not implemented")
