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


C.register_codes(dict(
    COMOPARATOR_NO_INSTANCE=N_("No comparator instance for '%(comparator)s' found")
    ))


def get_comparator(name):
    for entry in pkg_resources.iter_entry_points("object.comparator"):

        module = entry.load()
        if module.__name__ == name:
            return module

    raise KeyError(C.make_error("COMPARATOR_NO_INSTANCE", comparator=name))


class ElementComparator(object):

    def __init(self, obj):
        pass

    def process(self, *args, **kwargs):
        raise NotImplementedError(C.make_error('NOT_IMPLEMENTED', method="process"))

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
