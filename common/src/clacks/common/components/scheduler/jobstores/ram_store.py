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

"""
Stores jobs in an array in RAM. Provides no persistence support.
"""

from clacks.common.components.scheduler.jobstores.base import JobStore


class RAMJobStore(JobStore):

    def __init__(self):
        self.jobs = []

    def add_job(self, job):
        self.jobs.append(job)

    def update_job(self, job):
        pass

    def remove_job(self, job):
        self.jobs.remove(job)

    def load_jobs(self):
        pass

    def migrate_jobs(self, job, origin):
        pass

    def __repr__(self):
        return '<%s>' % (self.__class__.__name__)
