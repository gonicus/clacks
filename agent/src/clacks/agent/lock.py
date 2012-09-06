# -*- coding: utf-8 -*-
import time
import datetime
from inspect import stack
from clacks.common import Environment
from sqlalchemy.sql import select
from sqlalchemy import Table, Column, String, DateTime, MetaData


class LockError(Exception):
    pass


class GlobalLock(object):

    instance = None

    def __init__(self):
        self.env = Environment.getInstance()
        lck = self.env.config.get("locking.table", default="locks")
        self.__engine = self.env.getDatabaseEngine('core')

        metadata = MetaData()

        self.__locks = Table(lck, metadata,
            Column('id', String(128), primary_key=True),
            Column('node', String(1024)),
            Column('created', DateTime))

        metadata.create_all(self.__engine)

        # Establish the connection
        self.__conn = self.__engine.connect()

    def _exists(self, name):
        tmp = self.__conn.execute(select([self.__locks.c.id], self.__locks.c.id == name))
        res = bool(tmp.fetchone())
        tmp.close()
        return res

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

        self.__conn.execute(self.__locks.insert(), {
            'id': name,
            'node': self.env.id,
            'created': datetime.datetime.now(),
            })

        return True

    def _release(self, name):
        self.__conn.execute(self.__locks.delete().where(self.__locks.c.id == name))

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
