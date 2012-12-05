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
from clacks.common.utils import N_
from clacks.common.error import ClacksErrorHandler as C
from clacks.agent.exceptions import ElementFilterException


C.register_codes(dict(
    FILTER_NO_INSTANCE=N_("No filter instance for '%(filter)s' found")
    ))


def get_filter(name):
    for entry in pkg_resources.iter_entry_points("object.filter"):
        module = entry.load()
        if module.__name__ == name:
            return module

    raise KeyError(C.make_error("FILTER_NO_INSTANCE", name))


class ElementFilter(object):

    def __init__(self, obj):
        pass

    def process(self, obj, key, value):
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", method="process"))

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
