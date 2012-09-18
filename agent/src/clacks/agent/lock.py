# -*- coding: utf-8 -*-
import time
import datetime
from inspect import stack
from clacks.common import Environment
from pymongo import Connection


class LockError(Exception):
    pass


class GlobalLock(object):

    instance = None

    def __init__(self):
        self.env = Environment.getInstance()

        # Load db instance
        self.db = self.env.get_mongo_db('clacks')

    def _exists(self, name):
        if self.db.locks.find_one({'id': name}):
            return True
        return False

    def _acquire(self, name, blocking=True, timeout=None):
        if blocking:
            t0 = time.time()
            # Blocking, but we may have to wait
            while self._exists(name):
                time.sleep(1)
                if timeout and time.time() - t0 > timeout:
                    return False

        elif self._exists(name):
            # Non blocking, but exists
            return False

        self.db.locks.save({'id': name, 'node': self.env.id, 'created': datetime.datetime.now()})
        return True

    def _release(self, name):
        self.db.locks.remove({'id': name})

    @staticmethod
    def acquire(name=None, blocking=True, timeout=None):
        if not name:
            name = stack()[1][3]

        gl = GlobalLock.get_instance()
        return gl._acquire(name, blocking, timeout)

    @staticmethod
    def release(name=None):
        if not name:
            name = stack()[1][3]

        GlobalLock.get_instance()._release(name)

    @staticmethod
    def exists(name=None):
        if not name:
            name = stack()[1][3]

        return GlobalLock.get_instance()._exists(name)

    @staticmethod
    def get_instance():
        if not GlobalLock.instance:
            GlobalLock.instance = GlobalLock()

        return GlobalLock.instance
