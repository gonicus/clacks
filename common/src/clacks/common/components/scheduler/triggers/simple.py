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

from clacks.common.components.scheduler.util import convert_to_datetime


class SimpleTrigger(object):
    def __init__(self, run_date):
        self.run_date = convert_to_datetime(run_date)

    def get_next_fire_time(self, start_date):
        if self.run_date >= start_date:
            return self.run_date

    def __str__(self):
        return 'date[%s]' % str(self.run_date)

    def __repr__(self):
        return '<%s (run_date=%s)>' % (
            self.__class__.__name__, repr(self.run_date))
