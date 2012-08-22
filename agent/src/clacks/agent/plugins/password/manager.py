# -*- coding: utf-8 -*-
import pkg_resources
from clacks.common.components import Plugin
from clacks.common.components.command import Command
from clacks.common.utils import N_
from zope.interface import implements
from clacks.common.handler import IInterfaceHandler
from clacks.agent.objects.proxy import ObjectProxy
from clacks.common.components import PluginRegistry

class PasswordManager(Plugin):
    """
    Manager password changes
    """
    _priority_ = 91
    _target_ = 'password'

    methods = None
    instance = None
    implements(IInterfaceHandler)

    @staticmethod
    def get_instance():
        """
        Returns an instance of this object
        """
        if not PasswordManager.instance:
            PasswordManager.instance = PasswordManager()
        return PasswordManager.instance

    @Command(__help__=N_("Locks the account password for the given DN"))
    def lockAccountPassword(self, object_dn):
        """
        Locks the account password for the given DN
        """

        # Get the object for the given dn
        user = ObjectProxy(object_dn)

        # Check if there is a userPasswort available and set
        if not "userPassword" in user.get_attributes():
            raise Exception("object does not support userPassword attributes!")
        if not user.userPassword:
            raise Exception("no password set, cannot lock it")

        # Try to detect the responsible password method-class
        pwd_o = self.detect_method_by_hash(user.userPassword)
        if not pwd_o:
            raise Exception("Could not identify password method!")

        # Lock the hash and save it
        user.userPassword = pwd_o.lock_account(user.userPassword)
        user.commit()

    @Command(__help__=N_("Unlocks the account password for the given DN"))
    def unlockAccountPassword(self, object_dn):
        """
        Unlocks the account password for the given DN
        """

        # Get the object for the given dn and its used password method
        user = ObjectProxy(object_dn)

        # Check if there is a userPasswort available and set
        if not "userPassword" in user.get_attributes():
            raise Exception("object does not support userPassword attributes!")
        if not user.userPassword:
            raise Exception("no password set, cannot lock it")

        # Try to detect the responsible password method-class
        pwd_o = self.detect_method_by_hash(user.userPassword)
        if not pwd_o:
            raise Exception("Could not identify password method!")

        # Unlock the hash and save it
        user.userPassword = pwd_o.unlock_account(user.userPassword)
        user.commit()

    @Command(__help__=N_("Check whether the account can be locked or not"))
    def accountLockable(self, object_dn):
        index = PluginRegistry.getInstance("ObjectIndex")
        return len(index.xquery("collection('objects')/o:User[o:DN='%s' and "  \
                                "o:Attributes/o:userPassword and "             \
                                "o:Attributes/o:isLocked='false']/o:DN" % (object_dn))) != 0

    @Command(__help__=N_("Check whether the account can be unlocked or not"))
    def accountUnlockable(self, object_dn):
        index = PluginRegistry.getInstance("ObjectIndex")
        return len(index.xquery("collection('objects')/o:User[o:DN='%s' and "   \
                                "o:Attributes/o:userPassword and "              \
                                "o:Attributes/o:isLocked='true']/o:DN" % (object_dn))) != 0

    @Command(__help__=N_("Changes the used password enryption method"))
    def setUserPasswordMethod(self, object_dn, method, password):
        """
        Changes the used password encryption method
        """

        # Try to detect the responsible password method-class
        pwd_o = self.get_method_by_method_type(method)
        if not pwd_o:
            raise Exception("No password method found to generate hash of type '%s'!" % (method,))

        # Generate the new password hash usind the detected method
        pwd_str = pwd_o.generate_password_hash(password, method)

        # Set the password and commit the changes
        user = ObjectProxy(object_dn)
        user.userPassword = pwd_str
        user.commit()

    @Command(__help__=N_("Sets a new password for a user"))
    def setUserPassword(self, object_dn, password):
        """
        Set a new password for a user
        """
        user = ObjectProxy(object_dn)
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

    @Command(__help__=N_("List all password hashing-methods"))
    def listPasswordMethods(self):
        """
        Returns a list of all available password methods
        """
        return self.list_methods().keys()

    def detect_method_by_hash(self, hash_value):
        """
        Tries to find a password-method that is responsible for this kind of hashes
        """
        methods = self.list_methods()
        for hash_name in methods:
            if(methods[hash_name].is_responsible_for_password_hash(hash_value)):
                return methods[hash_name]
        return None

    def get_method_by_method_type(self, method_type):
        """
        Returns the passwod-method that is responsible for the given hashing-method

        e.g. get_method_by_method_type('crypt/blowfish')
        """
        methods = self.list_methods()
        return methods[method_type] if method_type in methods.keys() else None

    def list_methods(self):
        """
        Return a list of all useable password-hashing methods
        """

        # Build up a method hash map if not done before
        if not PasswordManager.methods:
            methods = {}

            # Walk through password methods and build up a hash-map
            for entry in pkg_resources.iter_entry_points("password.methods"):
                module = entry.load()()
                names = module.get_hash_names()
                if not names:
                    raise Exception("invalid hash-type for password method '%s' given!" % module.__class__.__name__)

                for name in names:
                    methods[name] = module
            PasswordManager.methods = methods

        return PasswordManager.methods
