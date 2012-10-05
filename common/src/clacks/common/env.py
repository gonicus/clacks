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
The environment module encapsulates the access of all
central information like logging, configuration management
and threads.

You can import it to your own code like this::

   >>> from clacks.common import Environment
   >>> env = Environment.getInstance()

--------
"""
import logging
import platform
from clacks.common.config import Config
from clacks.common.utils import parseURL
try:
    from sqlalchemy.orm import sessionmaker, scoped_session
    from sqlalchemy import create_engine
except ImportError:
    pass
try:
    from pymongo import Connection
except ImportError:
    pass

from clacks.common.utils import dmi_system


class Environment:
    """
    The global information container, used as a singleton.
    """
    threads = []
    locks = []
    id = None
    config = None
    log = None
    domain = ""
    reset_requested = False
    config = None
    noargs = False
    __instance = None
    __db = {}
    __xml_handler = None

    def __init__(self):
        # Load configuration
        self.config = Config(config=Environment.config, noargs=Environment.noargs)
        self.log = logging.getLogger(__name__)

        self.id = platform.node()

        # Dump configuration
        #TODO: core.loglevel is gone
        if self.config.get("core.loglevel") == "DEBUG":
            self.log.debug("configuration dump:")

            for section in self.config.getSections():
                self.log.debug("[%s]" % section)
                items = self.config.getOptions(section)

                for item in items:
                    self.log.debug("%s = %s" % (item, items[item]))

            self.log.debug("end of configuration dump")

        # Eventually etract the domain from the amqp url
        domain = 'org.clacks'
        tmp = self.config.get("amqp.url", default=None)
        if tmp:
            path = parseURL(tmp)['path']
            if path:
                domain = path

        # Initialized
        self.domain = self.config.get("core.domain", default=domain)
        self.uuid = self.config.get("core.id", default=None)
        if not self.uuid:
            self.log.warning("system has no id - falling back to configured hardware uuid")
            self.uuid = dmi_system("uuid")

            if not self.uuid:
                self.log.error("system has no id - please configure one in the core section")
                raise Exception("No system id found")

        self.active = True

        # Load base - an agent needs one, though
        self.base = self.config.get("core.base")

    def getDatabaseEngine(self, section, key="database"):
        """
        Return a database engine from the registry.

        ========= ============
        Parameter Description
        ========= ============
        section   name of the configuration section where the config is placed.
        key       optional value for the key where the database information is stored, defaults to *database*.
        ========= ============

        ``Return``: database engine
        """
        index = "%s.%s" % (section, key)

        if not index in self.__db:
            if not self.config.get(index):
                raise Exception("No database connection defined for '%s'!" % index)
            self.__db[index] = create_engine(self.config.get(index),
                    pool_size=40, pool_recycle=120)

        return self.__db[index]

    def getDatabaseSession(self, section, key="database"):
        """
        Return a database session from the pool.

        ========= ============
        Parameter Description
        ========= ============
        section   name of the configuration section where the config is placed.
        key       optional value for the key where the database information is stored, defaults to *database*.
        ========= ============

        ``Return``: database session
        """
        sql = self.getDatabaseEngine(section, key)
        session = scoped_session(sessionmaker(autoflush=True))
        session.configure(bind=sql)
        return session()

    def get_mongo_connection(self):
        mongo_uri = self.config.get("mongo.uri", default="localhost:27017")
        mongo_host, mongo_port = mongo_uri.split(':')
        return Connection(mongo_host, int(mongo_port))

    def get_mongo_db(self, collection):
        db = self.get_mongo_connection()[collection]

        # Check for authentication
        mongo_user = self.config.get("mongo.user")
        mongo_password = self.config.get("mongo.password")
        if mongo_user and mongo_password:
            db.authenticate(mongo_user, mongo_password)

        return db

    def requestRestart(self):
        self.log.warning("a component requested an environment reset")
        self.reset_requested = True
        self.active = False

    @staticmethod
    def getInstance():
        """
        Act like a singleton and return the
        :class:`clacks.common.env.Environment` instance.

        ``Return``: :class:`clacks.common.env.Environment`
        """
        if not Environment.__instance:
            Environment.__instance = Environment()
        return Environment.__instance

    @staticmethod
    def reset():
        if Environment.__instance:
            Environment.__instance = None
