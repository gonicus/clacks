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
from clacks.agent.error import ClacksErrorHandler as C


# Register the errors handled  by us
C.register_codes(dict(
    OPERATOR_NO_INSTANCE=N_("No operator instance for '%(operator)s' found")
    ))


def get_operator(name):
    for entry in pkg_resources.iter_entry_points("object.operator"):
        module = entry.load()
        if module.__name__ == name:
            return module

    raise KeyError(C.make_error("OPERATOR_NO_INSTANCE", None, operator=name))


class ElementOperator(object):

    def __init(self, obj):
        pass

    def process(self, *args, **kwargs):
        raise NotImplementedError(C.make_error("NOT_IMPLEMENTED", None, method="process"))
