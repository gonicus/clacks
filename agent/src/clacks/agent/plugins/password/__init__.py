# -*- coding: utf-8 -*-
__import__('pkg_resources').declare_namespace(__name__)


import pkg_resources
import re
from clacks.agent.objects.factory import STATUS_OK, STATUS_CHANGED
from clacks.agent.objects.filter import ElementFilter


class GeneratePasswordHash(ElementFilter):
    """
    Generates a new password hash.
    """
    def __init__(self, obj):
        super(GeneratePasswordHash, self).__init__(obj)

    def process(self, obj, key, valDict, method, is_locked):

        is_locked = is_locked == "True"

        # Get current pwdhash
        pwdhash = ""
        if valDict[key]['value']:
            pwdhash = valDict[key]['value'][0]

        # Generate new pwd hash
        if valDict[key]['status'] == STATUS_CHANGED:
            #pwdhash = "{%s}213GERSDF2351" % (method,)

            #TODO: Set passwort to secret - for testing
            pwdhash = "{CRYPT}$1$nDvjGkcB$PwJQibqWqVZMwa9c4scgh1"

        # Unlock account
        if pwdhash:
            if re.match(r'^{[^\}]+}!', pwdhash) and not is_locked:
                pwdhash = re.sub(r'^({[^\}]+})!(.*)$',"\\1\\2", pwdhash)
            elif not re.match(r'^{[^\}]+}!', pwdhash) and is_locked:
                pwdhash = re.sub(r'^({[^\}]+})(.*)$',"\\1!\\2", pwdhash)

        valDict[key]['value'] = [pwdhash]
        return key, valDict


class PasswordMethod(object):

    @staticmethod
    def list_methods():
        for entry in pkg_resources.iter_entry_points("password.methods"):
            module = entry.load()
            print module
            print entry
        print "ja"
        pass

    def is_locked():
        pass

    def lock_account():
        pass

    def unlock_account():
        pass

    def is_configurable():
        pass

    def get_hash_name():
        pass

    def is_responsible_for_password_hash(password_hash):
        pass

    def is_responsible_for_hash_name(hash_name):
        pass

    def generate_password_hash(new_password):
        pass


