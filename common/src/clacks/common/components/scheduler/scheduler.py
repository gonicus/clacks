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
This module is the main part of the library. It houses the Scheduler class
and related exceptions.
"""

from threading import Thread, Event, Lock
from datetime import datetime, timedelta
from logging import getLogger
import os
import sys
import inspect

from clacks.common.components.scheduler.util import * #@UnusedWildImport
from clacks.common.components.scheduler.triggers import SimpleTrigger, IntervalTrigger, CronTrigger
from clacks.common.components.scheduler.jobstores.ram_store import RAMJobStore
from clacks.common.components.scheduler.job import Job, MaxInstancesReachedError, JOB_RUNNING, JOB_ERROR, JOB_DONE
from clacks.common.components.scheduler.events import *
from clacks.common.components.scheduler.threadpool import ThreadPool

logger = getLogger(__name__)


class SchedulerAlreadyRunningError(Exception):
    """
    Raised when attempting to start or configure the scheduler when it's
    already running.
    """

    def __str__(self):
        return 'Scheduler is already running'


class Scheduler(object):
    """
    This class is responsible for scheduling jobs and triggering
    their execution.
    """

    _stopped = False
    _thread = None

    def __init__(self, gconfig={}, **options):
        self._wakeup = Event()
        self._jobstores = {}
        self._jobstores_lock = Lock()
        self._listeners = []
        self._listeners_lock = Lock()
        self._pending_jobs = []
        self.configure(gconfig, **options)

    def configure(self, gconfig={}, **options):
        """
        Reconfigures the scheduler with the given options. Can only be done
        when the scheduler isn't running.
        """
        if self.running:
            raise SchedulerAlreadyRunningError

        # Set general options
        config = combine_opts(gconfig, 'clacks.common.components.scheduler.', options)
        self.misfire_grace_time = int(config.pop('misfire_grace_time', 1))
        self.coalesce = asbool(config.pop('coalesce', True))
        self.daemonic = asbool(config.pop('daemonic', True))
        self.origin = config.pop('origin')

        # Configure the thread pool
        if 'threadpool' in config:
            self._threadpool = maybe_ref(config['threadpool'])
        else:
            threadpool_opts = combine_opts(config, 'threadpool.')
            self._threadpool = ThreadPool(**threadpool_opts)

        # Configure job stores
        jobstore_opts = combine_opts(config, 'jobstore.')
        jobstores = {}
        for key, value in jobstore_opts.items():
            store_name, option = key.split('.', 1)
            opts_dict = jobstores.setdefault(store_name, {})
            opts_dict[option] = value

        for alias, opts in jobstores.items():
            classname = opts.pop('class')
            cls = maybe_ref(classname)
            jobstore = cls(**opts)
            self.add_jobstore(jobstore, alias, True)

    def start(self):
        """
        Starts the scheduler in a new thread.
        """
        if self.running:
            raise SchedulerAlreadyRunningError

        # Create a RAMJobStore as the default if there is no default job store
        if not 'default' in self._jobstores:
            self.add_jobstore(RAMJobStore(), 'default', True)

        # Schedule all pending jobs
        for job, jobstore in self._pending_jobs:
            self._real_add_job(job, jobstore, False)
        del self._pending_jobs[:]

        self._stopped = False
        self._thread = Thread(target=self._main_loop, name='APScheduler')
        self._thread.setDaemon(self.daemonic)
        self._thread.start()

    def shutdown(self, wait=True, shutdown_threadpool=True, close_jobstores=True):
        """
        Shuts down the scheduler and terminates the thread.
        Does not interrupt any currently running jobs.

        :param wait: ``True`` to wait until all currently executing jobs have
                     finished (if ``shutdown_threadpool`` is also ``True``)
        :param shutdown_threadpool: ``True`` to shut down the thread pool
        :param close_jobstores: ``True`` to close all job stores after shutdown
        """
        if not self.running:
            return

        self._stopped = True
        self._wakeup.set()

        # Shut down the thread pool
        if shutdown_threadpool:
            self._threadpool.shutdown(wait)

        # Wait until the scheduler thread terminates
        self._thread.join()

        # Close all job stores
        if close_jobstores:
            for jobstore in itervalues(self._jobstores):
                jobstore.close()

    @property
    def running(self):
        return not self._stopped and self._thread and self._thread.isAlive()

    def add_jobstore(self, jobstore, alias, quiet=False):
        """
        Adds a job store to this scheduler.

        :param jobstore: job store to be added
        :param alias: alias for the job store
        :param quiet: True to suppress scheduler thread wakeup
        :type jobstore: instance of
            :class:`~clacks.common.components.scheduler.jobstores.base.JobStore`
        :type alias: str
        """
        self._jobstores_lock.acquire()
        try:
            if alias in self._jobstores:
                raise KeyError('Alias "%s" is already in use' % alias)
            self._jobstores[alias] = jobstore
            jobstore.load_jobs()
        finally:
            self._jobstores_lock.release()

        # Notify listeners that a new job store has been added
        self._notify_listeners(JobStoreEvent(EVENT_JOBSTORE_ADDED, alias))

        # Notify the scheduler so it can scan the new job store for jobs
        if not quiet:
            self._wakeup.set()

    def reschedule(self):
        self._wakeup.set()

    def refresh(self):
        for jobstore in itervalues(self._jobstores):
            jobstore.load_jobs()

        self._wakeup.set()

    def remove_jobstore(self, alias, close=True):
        """
        Removes the job store by the given alias from this scheduler.

        :type alias: str
        """
        self._jobstores_lock.acquire()
        try:
            jobstore = self._jobstores.pop(alias)
            if not jobstore:
                raise KeyError('No such job store: %s' % alias)

        finally:
            self._jobstores_lock.release()

        # Close the job store if requested
        if close:
            jobstore.close()

        # Notify listeners that a job store has been removed
        self._notify_listeners(JobStoreEvent(EVENT_JOBSTORE_REMOVED, alias))

    def add_listener(self, callback, mask=EVENT_ALL):
        """
        Adds a listener for scheduler events. When a matching event occurs,
        ``callback`` is executed with the event object as its sole argument.
        If the ``mask`` parameter is not provided, the callback will receive
        events of all types.

        :param callback: any callable that takes one argument
        :param mask: bitmask that indicates which events should be listened to
        """
        self._listeners_lock.acquire()
        try:
            self._listeners.append((callback, mask))
        finally:
            self._listeners_lock.release()

    def remove_listener(self, callback):
        """
        Removes a previously added event listener.
        """
        self._listeners_lock.acquire()
        try:
            for i, (cb, _) in enumerate(self._listeners):
                if callback == cb:
                    del self._listeners[i]
        finally:
            self._listeners_lock.release()

    def _notify_listeners(self, event):
        self._listeners_lock.acquire()
        try:
            listeners = tuple(self._listeners)
        finally:
            self._listeners_lock.release()

        for cb, mask in listeners:
            if event.code & mask:
                try:
                    cb(event)
                except:
                    logger.exception('error notifying listener')

    def _real_add_job(self, job, jobstore, wakeup):
        job.compute_next_run_time(datetime.now())
        job.origin = self.origin
        if not job.next_run_time:
            raise ValueError('Not adding job since it would never be run')

        self._jobstores_lock.acquire()
        try:
            try:
                store = self._jobstores[jobstore]
            except KeyError:
                raise KeyError('No such job store: %s' % jobstore)
            store.add_job(job)
        finally:
            self._jobstores_lock.release()

        # Notify listeners that a new job has been added
        event = JobStoreEvent(EVENT_JOBSTORE_JOB_ADDED, jobstore, job)
        self._notify_listeners(event)

        logger.info('added job "%s" to job store "%s"', job, jobstore)

        # Notify the scheduler about the new job
        if wakeup:
            self._wakeup.set()

    def add_job(self, trigger, func, args, kwargs, jobstore='default',
                **options):
        """
        Adds the given job to the job list and notifies the scheduler thread.

        :param trigger: trigger that determines when ``func`` is called
        :param func: callable to run at the given time
        :param args: list of positional arguments to call func with
        :param kwargs: dict of keyword arguments to call func with
        :param jobstore: alias of the job store to store the job in
        :rtype: :class:`~clacks.common.components.scheduler.job.Job`
        """
        job = Job(trigger, func, args or [], kwargs or {},
                  options.pop('misfire_grace_time', self.misfire_grace_time),
                  options.pop('coalesce', self.coalesce), **options)
        if not self.running:
            self._pending_jobs.append((job, jobstore))
            logger.info('adding job tentatively -- it will be properly '
                        'scheduled when the scheduler starts')
        else:
            self._real_add_job(job, jobstore, True)

        return job

    def _remove_job(self, job, alias, jobstore):
        jobstore.remove_job(job)

        # Notify listeners that a job has been removed
        event = JobStoreEvent(EVENT_JOBSTORE_JOB_REMOVED, alias, job)
        self._notify_listeners(event)

        logger.info('removed job "%s"', job)

    def add_date_job(self, func, date, args=None, kwargs=None, **options):
        """
        Schedules a job to be completed on a specific date and time.

        :param func: callable to run at the given time
        :param date: the date/time to run the job at
        :param name: name of the job
        :param jobstore: stored the job in the named (or given) job store
        :param misfire_grace_time: seconds after the designated run time that
            the job is still allowed to be run
        :type date: :class:`datetime.date`
        :rtype: :class:`~clacks.common.components.scheduler.job.Job`
        """
        trigger = SimpleTrigger(date)
        return self.add_job(trigger, func, args, kwargs, **options)

    def add_interval_job(self, func, weeks=0, days=0, hours=0, minutes=0,
                         seconds=0, start_date=None, args=None, kwargs=None,
                         **options):
        """
        Schedules a job to be completed on specified intervals.

        :param func: callable to run
        :param weeks: number of weeks to wait
        :param days: number of days to wait
        :param hours: number of hours to wait
        :param minutes: number of minutes to wait
        :param seconds: number of seconds to wait
        :param start_date: when to first execute the job and start the
            counter (default is after the given interval)
        :param args: list of positional arguments to call func with
        :param kwargs: dict of keyword arguments to call func with
        :param name: name of the job
        :param jobstore: alias of the job store to add the job to
        :param misfire_grace_time: seconds after the designated run time that
            the job is still allowed to be run
        :rtype: :class:`~clacks.common.components.scheduler.job.Job`
        """
        interval = timedelta(weeks=weeks, days=days, hours=hours,
                             minutes=minutes, seconds=seconds)
        trigger = IntervalTrigger(interval, start_date)
        return self.add_job(trigger, func, args, kwargs, **options)

    def add_cron_job(self, func, year=None, month=None, day=None, week=None,
                     day_of_week=None, hour=None, minute=None, second=None,
                     start_date=None, args=None, kwargs=None, **options):
        """
        Schedules a job to be completed on times that match the given
        expressions.

        :param func: callable to run
        :param year: year to run on
        :param month: month to run on
        :param day: day of month to run on
        :param week: week of the year to run on
        :param day_of_week: weekday to run on (0 = Monday)
        :param hour: hour to run on
        :param second: second to run on
        :param args: list of positional arguments to call func with
        :param kwargs: dict of keyword arguments to call func with
        :param name: name of the job
        :param jobstore: alias of the job store to add the job to
        :param misfire_grace_time: seconds after the designated run time that
            the job is still allowed to be run
        :return: the scheduled job
        :rtype: :class:`~clacks.common.components.scheduler.job.Job`
        """
        trigger = CronTrigger(year=year, month=month, day=day, week=week,
                              day_of_week=day_of_week, hour=hour,
                              minute=minute, second=second,
                              start_date=start_date)
        return self.add_job(trigger, func, args, kwargs, **options)

    def cron_schedule(self, **options):
        """
        Decorator version of :meth:`add_cron_job`.
        This decorator does not wrap its host function.
        Unscheduling decorated functions is possible by passing the ``job``
        attribute of the scheduled function to :meth:`unschedule_job`.
        """
        def inner(func):
            func.job = self.add_cron_job(func, **options)
            return func
        return inner

    def interval_schedule(self, **options):
        """
        Decorator version of :meth:`add_interval_job`.
        This decorator does not wrap its host function.
        Unscheduling decorated functions is possible by passing the ``job``
        attribute of the scheduled function to :meth:`unschedule_job`.
        """
        def inner(func):
            func.job = self.add_interval_job(func, **options)
            return func
        return inner

    def get_jobs(self):
        """
        Returns a list of locally scheduled jobs.

        :return: list of :class:`~clacks.common.components.scheduler.job.Job` objects
        """
        self._jobstores_lock.acquire()
        try:
            jobs = []
            for jobstore in itervalues(self._jobstores):
                jobs.extend(jobstore.jobs)
            return jobs
        finally:
            self._jobstores_lock.release()

    def unschedule_job(self, job):
        """
        Removes a job, preventing it from being run any more.
        """
        self._jobstores_lock.acquire()
        try:
            for alias, jobstore in iteritems(self._jobstores):
                if job in list(jobstore.jobs):
                    self._remove_job(job, alias, jobstore)
                    return
        finally:
            self._jobstores_lock.release()

        raise KeyError('Job "%s" is not scheduled in any job store' % job)

    def unschedule_func(self, func):
        """
        Removes all jobs that would execute the given function.
        """
        found = False
        self._jobstores_lock.acquire()
        try:
            for alias, jobstore in iteritems(self._jobstores):
                for job in list(jobstore.jobs):
                    if job.func == func:
                        self._remove_job(job, alias, jobstore)
                        found = True
        finally:
            self._jobstores_lock.release()

        if not found:
            raise KeyError('The given function is not scheduled in this '
                           'scheduler')

    def get_job_by_id(self, job_id):
        job_object = None

        self._jobstores_lock.acquire()
        try:
            for jobstore in iteritems(self._jobstores).values():
                if jobstore.jobs:
                    for job in jobstore.jobs:
                        if job.uuid == job_id:
                            job_object = job
                            break

                if job_object:
                    break

        finally:
            self._jobstores_lock.release()

        return job_object

    def print_jobs(self, out=None):
        """
        Prints out a textual listing of all jobs currently scheduled on this
        scheduler.

        :param out: a file-like object to print to (defaults to **sys.stdout**
                    if nothing is given)
        """
        out = out or sys.stdout
        job_strs = []
        self._jobstores_lock.acquire()
        try:
            for alias, jobstore in iteritems(self._jobstores):
                job_strs.append('Jobstore %s:' % alias)
                if jobstore.jobs:
                    for job in jobstore.jobs:
                        job_strs.append('    %s' % job)
                else:
                    job_strs.append('    No scheduled jobs')
        finally:
            self._jobstores_lock.release()

        out.write(os.linesep.join(job_strs) + os.linesep)

    def _run_job(self, job, run_times):
        """
        Acts as a harness that runs the actual job code in a thread.
        """
        for run_time in run_times:
            # See if the job missed its run time window, and handle possible
            # misfires accordingly
            difference = datetime.now() - run_time
            grace_time = timedelta(seconds=job.misfire_grace_time)
            if difference > grace_time:
                # Notify listeners about a missed run
                event = JobEvent(EVENT_JOB_MISSED, job, run_time)
                self._notify_listeners(event)
                logger.warning('run time of job "%s" was missed by %s',
                               job, difference)
            else:
                try:
                    job.add_instance()
                except MaxInstancesReachedError:
                    event = JobEvent(EVENT_JOB_MISSED, job, run_time)
                    self._notify_listeners(event)
                    logger.warning('execution of job "%s" skipped: '
                                   'maximum number of running instances '
                                   'reached (%d)', job, job.max_instances)
                    break

                logger.debug('running job "%s" (scheduled at %s)', job,
                            run_time)

                try:
                    job.status = JOB_RUNNING
                    retval = job.func(*job.args, **job.kwargs)
                    job.progress = 100
                    job.status = JOB_DONE

                except Exception as e:
                    job.status = JOB_ERROR

                    # Notify listeners about the exception
                    exc, tb = sys.exc_info()[1:]

                    event = JobEvent(EVENT_JOB_ERROR, job, run_time,
                                     exception=exc, traceback=tb)
                    self._notify_listeners(event)

                    logger.error('job "%s" raised an exception' % job)
                    logger.exception(e)

                else:
                    # Run direct callback?
                    if job.callback:
                        job.callback(job, run_time, retval=retval)

                    # Notify listeners about successful execution
                    event = JobEvent(EVENT_JOB_EXECUTED, job, run_time,
                                     retval=retval)
                    self._notify_listeners(event)

                    logger.debug('job "%s" executed successfully', job)

                job.remove_instance()

                # If coalescing is enabled, don't attempt any further runs
                if job.coalesce:
                    break

    def migrate_job(self, job):
        for jobstore in iteritems(self._jobstores).values():
            if jobstore.jobs and job in jobstore.jobs:
                jobstore.migrate_job(job, self.origin)
                break

        self.reschedule()

    def _process_jobs(self, now):
        """
        Iterates through jobs in every jobstore, starts pending jobs
        and figures out the next wakeup time.
        """
        next_wakeup_time = None
        self._jobstores_lock.acquire()
        try:
            for alias, jobstore in iteritems(self._jobstores):
                for job in tuple(jobstore.jobs):
                    run_times = job.get_run_times(now)

                    if run_times:
                        # Continue if this is not our job. Should be completely handled by
                        # other nodes.
                        if job.origin != self.origin:
                            continue

                        self._threadpool.submit(self._run_job, job, run_times)

                        # Increase the job's run count
                        if job.coalesce:
                            job.runs += 1
                        else:
                            job.runs += len(run_times)

                        # Update the job, but don't keep finished jobs around
                        if job.compute_next_run_time(now + timedelta(microseconds=1)):
                            jobstore.update_job(job)
                        else:
                            self._remove_job(job, alias, jobstore)

                    if not next_wakeup_time:
                        next_wakeup_time = job.next_run_time
                    elif job.next_run_time:
                        next_wakeup_time = min(next_wakeup_time,
                                               job.next_run_time)
            return next_wakeup_time
        finally:
            self._jobstores_lock.release()

    def _main_loop(self):
        """Executes jobs on schedule."""

        logger.info('starting scheduler')
        self._notify_listeners(SchedulerEvent(EVENT_SCHEDULER_START))

        self._wakeup.clear()
        while not self._stopped:
            logger.debug('looking for jobs to run')
            now = datetime.now()
            next_wakeup_time = self._process_jobs(now)

            # Sleep until the next job is scheduled to be run,
            # a new job is added or the scheduler is stopped
            if next_wakeup_time is not None:
                wait_seconds = time_difference(next_wakeup_time, now)
                logger.debug('next wakeup is due at %s (in %f seconds)',
                             next_wakeup_time, wait_seconds)
                self._wakeup.wait(wait_seconds)
            else:
                logger.debug('no jobs; waiting until a job is added')
                self._wakeup.wait()
            self._wakeup.clear()

        logger.info('scheduler has been shut down')
        self._notify_listeners(SchedulerEvent(EVENT_SCHEDULER_SHUTDOWN))


def set_job_property(key, value):
    """
    Set given job property to value.
    """
    for level in range(2, 10):
        f = sys._getframe(level)
        local_vars = inspect.getargvalues(f)[3]
        if 'job' in local_vars and 'self' in local_vars and \
                local_vars['self'].__class__.__name__ == "Scheduler":
            setattr(local_vars['job'], key, value)
            return

    raise Exception("cannot find parent job to set progress for")
