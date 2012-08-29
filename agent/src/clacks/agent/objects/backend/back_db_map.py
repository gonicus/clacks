# -*- coding: utf-8 -*-
from clacks.agent.objects.backend import ObjectBackend
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, BLOB, DateTime
from clacks.common import Environment
from logging import getLogger


class DBMapBackendError(Exception):
    pass


class DBMAP(ObjectBackend):

    env = None
    log = None

    def __init__(self):

        # Initialize environment and logger
        self.env = Environment.getInstance()
        self.log = getLogger(__name__)

    def execute_actions(self, data, params):

        # Read storage path from config
        con_str = self.env.config.get("sql.backend_connection", None)
        if not con_str:
            raise DBMapBackendError("no sql.backend_connection found in config file")

        # Extract action per connection
        connections = {}
        actions = {}
        for attribute in data:
            for item in data[attribute]["value"]:
                for database in item:

                    # Try to find a database connection for the DB
                    con_str = self.env.config.get("backend_dbmap.%s" % (database.replace(".", "_")), None)
                    if not con_str:
                        raise DBMapBackendError("no database connection specified for %s! Please add config parameters for %s" % \
                              (database, "backend_dbmap.%s" % (database.replace(".", "_"))))

                    # Try to establish the connection
                    engine = create_engine(con_str)
                    if database not in connections:
                        connections[database] = engine
                        actions[database] = []
                    actions[database] += item[database]

            # Execute actions on the database connection, as transaction
            for database in actions:
                with connections[database].begin() as conn:
                    for action in actions[database]:
                        try:
                            conn.execute(action)
                        except Exception as e:
                            raise DBMapBackendError("failed to execute SQL statement '%s' on database '%s': %s" % (str(action), database, str(e)))


    def load(self, uuid, info, back_attrs=None):
        return {}

    def identify(self, dn, params, fixed_rdn=None):
        return False

    def identify_by_uuid(self, uuid, params):
        return False

    def exists(self, misc):
        return False

    def remove(self, uuid, data, params):
        return True

    def retract(self, uuid, data, params):
        self.execute_actions(data, params)

    def extend(self, uuid, data, params, foreign_keys):
        self.execute_actions(data, params)

    def move_extension(self, uuid, new_base):
        pass

    def move(self, uuid, new_base):
        return True

    def create(self, base, data, params, foreign_keys=None):
        return None

    def update(self, uuid, data, params):
        return True

    def is_uniq(self, attr, value, at_type):
        return False

    def query(self, base, scope, params, fixed_rdn=None):
        return []
