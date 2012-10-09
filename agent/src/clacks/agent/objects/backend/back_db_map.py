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

from clacks.agent.objects.backend import ObjectBackend, BackendError
from sqlalchemy import create_engine
from clacks.common import Environment
from clacks.common.utils import N_
from clacks.agent.error import ClacksErrorHandler as C
from logging import getLogger


# Register the errors handled  by us
C.register_codes(dict(
    SQL_QUERY_ERROR=N_("Failed to execute SQL statement '%(action)s' on database '%(database)s'")
    ))


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
            raise BackendError(C.make_error("DB_CONFIG_MISSING", target="sql.backend_connection"))

        # Extract action per connection
        connections = {}
        actions = {}
        for attribute in data:
            for item in data[attribute]["value"]:
                for database in item:

                    # Try to find a database connection for the DB
                    con_str = self.env.config.get("backend_dbmap.%s" % (database.replace(".", "_")), None)
                    if not con_str:
                        raise BackendError(C.make_error("DB_CONFIG_MISSING", target="backend_dbmap.%s" % database.replace(".", "_")))

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
                            raise BackendError(C.make_error("SQL_QUERY_ERROR", action=str(action), database=database))

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
