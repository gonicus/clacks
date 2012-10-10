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
from clacks.common.error import ClacksErrorHandler as C


def get_renderers():
    res = {}
    for entry in pkg_resources.iter_entry_points("object.renderer"):
        module = entry.load()
        res[module.getName()] = module.render

    return res


class ResultRenderer(object):

    @staticmethod
    def getName():
        raise NotImplementedError(C.make_error('NOT_IMPLEMENTED', method="getName"))

    @staticmethod
    def render(value):
        raise NotImplementedError(C.make_error('NOT_IMPLEMENTED', method="render"))
