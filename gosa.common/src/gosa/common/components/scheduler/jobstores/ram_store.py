"""
Stores jobs in an array in RAM. Provides no persistence support.
"""

from gosa.common.components.scheduler.jobstores.base import JobStore


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
