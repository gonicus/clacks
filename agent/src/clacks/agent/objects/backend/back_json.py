# -*- coding: utf-8 -*-
import os
from clacks.agent.objects.backend import ObjectBackend
from json import loads, dumps
from logging import getLogger
from clacks.common import Environment


class JSON(ObjectBackend):

    data = None

    def __init__(self):

        # Initialize environment and logger
        self.env = Environment.getInstance()
        self.log = getLogger(__name__)

        # Read storage path from config
        self._file_path = self.env.config.get("json.database_file", None)

        # Create a json file on demand
        if not os.path.exists(self._file_path):
            open(self._file_path, "w").write(dumps({}))

    def __load(self):
        """
        Loads the json file and returns a object
        """
        return loads(open(self._file_path).read())

    def __save(self, json):
        """
        Saves back the given object to the json file.
        """
        open(self._file_path, "w").write(dumps(json))

    def load(self, uuid, info):
        """
        Load object properties for the given uuid
        """
        json = self.__load()
        data = {}
        if uuid in json:
            for plug in json[uuid]:
                data = dict(data.items() + json[uuid][plug].items())

            return data
        return {}

    def identify(self, dn, params, fixed_rdn=None):
        """
        Identify an object by dn
        """
        return False

    def identify_by_uuid(self, uuid, params):
        """
        Identify an object by uuid
        """
        json = self.__load()
        if uuid in json and params['type'] in json[uuid].keys():
            return True

        return False

    def retract(self, uuid, data, params):
        """
        Remove an object extension
        """
        json = self.__load()
        if uuid in json:
            del(json[uuid])
        self.__save(json)

    def extend(self, uuid, data, params, foreign_keys):
        """
        Create an object extension
        """
        json = self.__load()
        json[uuid] = {}
        json[uuid][params['type']] = {}
        for item in data:
            json[uuid][params['type']][item]= data[item]['value']
        self.__save(json)

    def dn2uuid(self, dn):
        return None

    def uuid2dn(self, uuid):
        return None

    def move_extension(self, uuid, new_base):
        pass

    def move(self, uuid, new_base):
        return True

    def update(self, uuid, data):
        print "Update:", uuid
        return True

    def is_uniq(self, attr, value, at_type):
        return False

    def query(self, base, scope, params, fixed_rdn=None):
        print "Query:", base
        return []

    def exists(self, misc):
        print "Exists:", misc
        return False

    def remove(self, uuid, recursive=False):
        print "Remove:", uuid
        return True

    def create(self, base, data, params, foreign_keys=None):
        print "Create:", base
        return None
