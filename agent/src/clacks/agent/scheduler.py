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
The scheduler service can be used to do time based - time-phased, periodic, single shot - tasks
which may be scheduled by a user or by indirectly by a script or the web frontend.

    >>> proxy.schedulerGetJobs()
    {u'b4b54880-dac9-11e0-b58e-5452005f1250': {u'next_run_time':
    u'20110909115527', u'name': u'SchedulerService.migrate',
    u'misfire_grace_time': 1, u'job_type': None, u'max_instances': 1,
    u'max_runs': None, u'coalesce': True, u'tag': u'_internal', u'owner': None,
    u'description': None}}

    >>> proxy.schedulerGetJobs({'tag':'service'})
    {}

    >>> proxy.schedulerAddDateJob("notifyUser", ["cajus", "test", "test"], None, "20110909131212")
    u'596b8f2e-dad4-11e0-bcf1-5452005f1250'

------
"""
import logging
from zope.interface import implements
from datetime import datetime, timedelta
from clacks.common.handler import IInterfaceHandler
from clacks.common import Environment
from clacks.common.utils import N_
from clacks.common.event import EventMaker
from clacks.common.components import Command, PluginRegistry, Plugin
from clacks.common.components.scheduler import Scheduler
from clacks.common.components.scheduler.job import JOB_RUNNING
from clacks.common.components.scheduler.jobstores.mongodb_store import MongoDBJobStore
from clacks.common.components.scheduler.jobstores.ram_store import RAMJobStore
from clacks.common.components.scheduler.triggers import SimpleTrigger, IntervalTrigger, CronTrigger
from clacks.common.components.scheduler.events import EVENT_JOBSTORE_JOB_REMOVED, EVENT_JOBSTORE_JOB_ADDED, EVENT_JOB_EXECUTED
from clacks.common.components.amqp import EventConsumer


class SchedulerService(Plugin):
    """
    The scheduler service provider.
    """

    implements(IInterfaceHandler)
    _priority_ = 0

    # Target queue
    _target_ = 'core'

    def __init__(self):
        env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.debug("initializing scheduler")
        self.env = env

        self.sched = Scheduler(origin=self.env.id)

        self.sched.add_jobstore(MongoDBJobStore(
            database='clacks',
            collection='scheduler',
            connection=self.env.get_mongo_connection()), 'default')
        self.sched.add_jobstore(RAMJobStore(), 'ram', True)

    def getScheduler(self):
        return self.sched

    def serve(self):
        """
        Start the scheduler service.
        """
        self.sched.start()

        # Start migration job
        self.sched.add_interval_job(self.migrate, seconds=60, tag='_internal',
                jobstore="ram")

        # Notify others about local scheduler job changes
        self.sched.add_listener(self.__notify, EVENT_JOBSTORE_JOB_REMOVED |
                EVENT_JOBSTORE_JOB_ADDED | EVENT_JOB_EXECUTED)

        # Get notified by others about remote job changes
        amqp = PluginRegistry.getInstance("AMQPHandler")
        EventConsumer(self.env,
            amqp.getConnection(),
            xquery="""
                declare namespace f='http://www.gonicus.de/Events';
                let $e := ./f:Event
                return $e/f:SchedulerUpdate
                    and $e/f:Id != '%s'
            """ % self.env.id,
            callback=self.__eventProcessor)

    def stop(self):
        """ Stop scheduler service. """
        self.sched.shutdown()

    def migrate(self):
        self.log.debug("scheduler: looking for stale jobs")
        grace = datetime.now() + timedelta(seconds=int(self.env.config.get('scheduler.gracetime', default='30')))
        count = 0

        # Find jobs that are expired for a defined grace time.
        for job in self.sched.get_jobs():
            if job.origin != self.env.id and job.next_run_time and job.next_run_time < grace:
                self.sched.migrate_job(job)
                count += 1

        # Tell others to reload their jobs
        if count:
            self.__notify()

    @Command(__help__=N_("List jobs matchings an optional filter."))
    def schedulerGetJobs(self, fltr=None):
        """
        List available jobs with filtering for job properties.

        Example:

            >>> proxy.schedulerGetJobs()
            {u'b4b54880-dac9-11e0-b58e-5452005f1250': {
                u'next_run_time': u'20110909115527',
                u'name': u'SchedulerService.migrate',
                u'misfire_grace_time': 1,
                u'job_type': None,
                u'max_instances': 1,
                u'max_runs': None,
                u'coalesce': True,
                u'tag': u'\_internal',
                u'owner': None,
                u'description': None}}
            >>> proxy.schedulerGetJobs({'tag':'service'})
            {}

        =========== ===============================================
        Parameter   Description
        =========== ===============================================
        fltr        Dictionary containing job options to filter for
        =========== ===============================================

        ``Return:`` Dictionary of jobs, indexed by job id
        """
        res = {}

        for job in self.sched.get_jobs():
            job_dict = dict([(key, getattr(job, key)) for key in [
                'misfire_grace_time',
                'coalesce',
                'name',
                'max_runs',
                'max_instances',
                'tag',
                'owner',
                'job_type',
                'description']])

            # Add next run time if available
            job_dict['next_run_time'] = job.next_run_time.strftime("%Y%m%d%H%M%S") if job.next_run_time else None

            if fltr:
                hits = 0
                for key, value in fltr.items():
                    if getattr(job, key) == value:
                        hits += 1
                if hits == len(fltr):
                    res[job.uuid] = job_dict

            else:
                res[job.uuid] = job_dict

        return res

    @Command(needsQueue=True, needsUser=True, __help__=N_("Add a new date based job to the scheduler."))
    def schedulerAddDateJob(self, user, queue, func, args, kwargs, date, **options):
        """
        Add a new job triggered at a specified date.

        =========== =======================================
        Parameter   Description
        =========== =======================================
        func        Function *pointer*
        args        Function arguments
        kwargs      Function keyword arguments
        date        Execution date of the function
        options     Set of job options
        =========== =======================================

        A job can have these options:

        =================== ===============================================================================
        Option              Description
        =================== ===============================================================================
        name                Job name
        description         Description of the job
        tag                 Free choosable text tag to make it easier to find jobs
        progress            Automatically maintained
        misfire_grace_time  seconds after the designated run time that the job is still allowed to be run
        coalesce            Roll several pending executions of jobs into one
        max_runs            Maximum number of times this job is allowed to be triggered
        max_instances       Maximum number of concurrently running instances allowed for this job
        callback            Function to be called after the job has been done
        =================== ===============================================================================

        `Return:` Job ID
        """
        options['owner'] = user
        options['job_type'] = 'date'
        date = datetime.strptime(date, '%Y%m%d%H%M%S')

        # Load CommandRegistry dispatcher to schedule with that method
        cr = PluginRegistry.getInstance("CommandRegistry")
        args = [user, queue, func] + args

        trigger = SimpleTrigger(date)
        job = self.sched.add_job(trigger, cr.dispatch, args, kwargs, **options)
        return job.uuid

    @Command(needsQueue=True, needsUser=True, __help__=N_("Add a new cron based job to the scheduler."))
    def schedulerCronDateJob(self, user, queue, func, args, kwargs, year=None, month=None,
            day=None, week=None, day_of_week=None, hour=None, minute=None, second=None,
            start_date=None, **options):
        """
        Add a new job triggered in a cron style manner.

        =========== =======================================
        Parameter   Description
        =========== =======================================
        func        Function *pointer*
        args        Function arguments
        kwargs      Function keyword arguments
        year        Year to run on
        month       Month to run on
        day         Day of month to run on
        week        Week of the year to run on
        day_of_week Weekday to run on (0 = Monday)
        hour        Hour to run on
        second      Second to run on
        options     Set of job options
        =========== =======================================

        For an option description, see :meth:`clacks.agent.scheduler.SchedulerService.schedulerDateJob`.

        `Return:` Job ID
        """
        options['owner'] = user
        options['job_type'] = 'cron'
        start_date = datetime.strptime(start_date, '%Y%m%d%H%M%S')

        # Load CommandRegistry dispatcher to schedule with that method
        cr = PluginRegistry.getInstance("CommandRegistry")
        args = [user, queue, func] + args

        trigger = CronTrigger(year=year, month=month, day=day, week=week,
                day_of_week=day_of_week, hour=hour,
                minute=minute, second=second,
                start_date=start_date)
        job = self.sched.add_job(trigger, cr.dispatch, args, kwargs, **options)
        return job.uuid

    @Command(needsQueue=True, needsUser=True, __help__=N_("Add a new interval job to the scheduler."))
    def schedulerIntervalJob(self, user, queue, func, args, kwargs, weeks=0, days=0, hours=0,
            minutes=0, seconds=0, start_date=None, **options):
        """
        Add a new job triggered in a specified interval.

        =========== =======================================
        Parameter   Description
        =========== =======================================
        func        Function *pointer*
        args        Function arguments
        kwargs      Function keyword arguments
        weeks       Number of weeks to wait
        days        Number of days to wait
        hours       Number of hours to wait
        minutes     Number of minutes to wait
        seconds     Number of seconds to wait
        start_date  When to first execute the job
        options     Set of job options
        =========== =======================================

        For an option description, see :meth:`clacks.agent.scheduler.SchedulerService.schedulerDateJob`.

        `Return:` Job ID
        """
        options['owner'] = user
        options['job_type'] = 'interval'
        start_date = datetime.strptime(start_date, '%Y%m%d%H%M%S')

        # Load CommandRegistry dispatcher to schedule with that method
        cr = PluginRegistry.getInstance("CommandRegistry")
        args = [user, queue, func] + args

        interval = timedelta(weeks=weeks, days=days, hours=hours,
                minutes=minutes, seconds=seconds)
        trigger = IntervalTrigger(interval, start_date)
        job = self.sched.add_job(trigger, cr.dispatch, args, kwargs, **options)
        return job.uuid

    @Command(needsUser=True, __help__=N_("Remove job from the scheduler."))
    def schedulerRemoveJob(self, user, job_id):
        """
        Remove a job by it's job ID.

        =========== =======================================
        Parameter   Description
        =========== =======================================
        job_id      The job ID
        =========== =======================================

        ``Return:`` True on success
        """
        job = self.sched.get_job_by_id(job_id)
        if job.status == JOB_RUNNING:
            return False

        self.sched.unschedule_job(job)
        return True

    def __notify(self, event=None):
        # Don't send events for internal job changes
        if event and event.job.tag == '_internal':
            return

        e = EventMaker()
        notify = e.Event(e.SchedulerUpdate(e.Id(self.env.id)))
        amqp = PluginRegistry.getInstance("AMQPHandler")
        amqp.sendEvent(notify)

    def __eventProcessor(self, data):
        self.sched.refresh()
