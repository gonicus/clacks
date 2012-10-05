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

from clacks.agent.objects.operator import ElementOperator


class And(ElementOperator):

    def __init__(self, obj):
        super(And, self).__init__()

    def process(self, v1, v2):
        return v1 and v2


class Or(ElementOperator):

    def __init__(self, obj):
        super(Or, self).__init__()

    def process(self, v1, v2):
        return v1 or v2


class Not(ElementOperator):

    def __init__(self, obj):
        super(Not, self).__init__()

    def process(self, a):
        return not a
