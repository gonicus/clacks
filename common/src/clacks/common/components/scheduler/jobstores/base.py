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
Abstract base class that provides the interface needed by all job stores.
Job store methods are also documented here.
"""


class JobStore(object):

    def add_job(self, job):
        """Adds the given job from this store."""
        raise NotImplementedError

    def update_job(self, job):
        """Persists the running state of the given job."""
        raise NotImplementedError

    def remove_job(self, job):
        """Removes the given jobs from this store."""
        raise NotImplementedError

    def load_jobs(self):
        """Loads jobs from this store into memory."""
        raise NotImplementedError

    def migrate_jobs(self, job, origin):
        """Migrate job to new origin."""
        raise NotImplementedError

    def close(self):
        """Frees any resources still bound to this job store."""
