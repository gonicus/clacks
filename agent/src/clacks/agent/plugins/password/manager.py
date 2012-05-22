# -*- coding: utf-8 -*-
import pkg_resources

class PasswordManager(object):

    methods = None
    instance = None

    @staticmethod
    def get_instance():
        if not PasswordManager.instance:
            PasswordManager.instance = PasswordManager()
        return PasswordManager.instance

    def detect_method_by_hash(self, hash_value):
        methods = self.list_methods()
        for hash_name in methods:
            if(methods[hash_name].is_responsible_for_password_hash(hash_value)):
                return methods[hash_name]
        return None

    def get_method_by_hash(self, hash_name):
        methods = self.list_methods()
        return methods[hash_name] if hash_name in methods else None

    def list_methods(self):
        if not PasswordManager.methods:
            methods = {}
            for entry in pkg_resources.iter_entry_points("password.methods"):
                module = entry.load()()
                names = module.get_hash_names()
                if not names:
                    raise Exception("invalid hash-type for password method '%s' given!" % module.__class__.__name__)

                for name in names:
                  methods[name] = module
            PasswordManager.methods = methods
        return PasswordManager.methods
