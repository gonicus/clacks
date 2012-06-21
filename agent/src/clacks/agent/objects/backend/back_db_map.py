# -*- coding: utf-8 -*-
from clacks.agent.objects.backend import ObjectBackend
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, BLOB, DateTime


class DBMAP(ObjectBackend):

    def __init__(self):
        pass

    def load(self, uuid, info):
        return {}

    def identify(self, dn, params, fixed_rdn=None):
        return False

    def identify_by_uuid(self, uuid, params):
        return False

    def exists(self, misc):
        return False

    def remove(self, uuid, recursive=False):
        return True

    def retract(self, uuid, data, params):
        pass

    def extend(self, uuid, data, params, foreign_keys):

        # Establish database connection
        engine = create_engine("mysql://root:secret@localhost/gophone" + "?charset=utf8&sql_mode=STRICT_ALL_TABLES")

        # Start transactional processing of sql-alchemy commands
        try:
            with engine.begin() as conn:
                for attribute in data:
                    for item in data[attribute]['value']:
                        try:
                            conn.execute(item)
                            print "Ja"
                        except Exception as e:
                            print "Huh?", e
        except:
            print "hmm?"

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
