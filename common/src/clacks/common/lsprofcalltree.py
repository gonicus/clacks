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

from __future__ import print_function


def label(code):
    if isinstance(code, str):
        return ('~', 0, code)    # built-in functions ('~' sorts at the end)
    else:
        return '%s %s:%d' % (code.co_name, code.co_filename, code.co_firstlineno)


class KCacheGrind(object):
    def __init__(self, profiler):
        self.data = profiler.getstats()
        self.out_file = None

    def output(self, out_file):
        self.out_file = out_file
        print('events: Ticks', file=out_file)
        self._print_summary()
        for entry in self.data:
            self._entry(entry)

    def _print_summary(self):
        max_cost = 0
        for entry in self.data:
            totaltime = int(entry.totaltime * 1000)
            max_cost = max(max_cost, totaltime)
        print('summary: %d' % (max_cost,), file=self.out_file)

    def _entry(self, entry):
        out_file = self.out_file
        code = entry.code
        inlinetime = int(entry.inlinetime * 1000)
        if isinstance(code, str):
            print('fi=~', file=out_file)
        else:
            print('fi=%s' % (code.co_filename,), file=out_file)
        print('fn=%s' % (label(code),), file=out_file)
        if isinstance(code, str):
            print('0 ', inlinetime, file=out_file)
        else:
            print('%d %d' % (code.co_firstlineno, inlinetime), file=out_file)
        # recursive calls are counted in entry.calls
        if entry.calls:
            calls = entry.calls
        else:
            calls = []
        if isinstance(code, str):
            lineno = 0
        else:
            lineno = code.co_firstlineno
        for subentry in calls:
            self._subentry(lineno, subentry)
        print(file=out_file)

    def _subentry(self, lineno, subentry):
        out_file = self.out_file
        code = subentry.code
        totaltime = int(subentry.totaltime * 1000)
        print('cfn=%s' % (label(code),), file=out_file)
        if isinstance(code, str):
            print('cfi=~', file=out_file)
            print('calls=%d 0' % (subentry.callcount,), file=out_file)
        else:
            print('cfi=%s' % (code.co_filename,), file=out_file)
            print('calls=%d %d' % (
                subentry.callcount, code.co_firstlineno), file=out_file)
        print('%d %d' % (lineno, totaltime), file=out_file)
