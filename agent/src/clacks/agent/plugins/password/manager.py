# -*- coding: utf-8 -*-
import pkg_resources
from clacks.common.components import Plugin
from clacks.common.components.command import Command
from clacks.common.utils import stripNs, N_
from zope.interface import implements
from clacks.common.handler import IInterfaceHandler
from clacks.agent.objects.proxy import ObjectProxy


class PasswordManager(Plugin):
    """
    Manager password changes
    """
    _priority_ = 91
    _target_ = 'password'

    methods = None
    instance = None
    implements(IInterfaceHandler)

    @Command(__help__=N_("Sets a new password for a user"))
    def setUserPassword(self, dn, password):
        """
        Set a new password for a user
        """
        user = ObjectProxy(dn)
        method = user.passwordMethod

        # Try to detect the responsible password method-class
        pwd_o = self.get_method_by_method_type(method)
        if not pwd_o:
            raise Exception("No password method found to generate hash of type '%s'!" % (method,))

        # Generate the new password hash usind the detected method
        pwd_str = pwd_o.generate_password_hash(password, method)

        # Set the password and commit the changes
        user.userPassword = pwd_str
        user.commit()

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

    def get_method_by_method_type(self, method_type):
        methods = self.list_methods()
        return methods[method_type] if method_type in methods.keys() else None

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
