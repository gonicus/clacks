from clacks.agent.objects.factory import STATUS_OK, STATUS_CHANGED
from clacks.agent.objects.filter import ElementFilter
from clacks.agent.plugins.password.manager import PasswordManager
import re


class GeneratePasswordHash(ElementFilter):
    """
    Generates a new password hash.
    """
    def __init__(self, obj):
        super(GeneratePasswordHash, self).__init__(obj)

    def process(self, obj, key, valDict):

        # Get required informations to set a new password
        is_locked = valDict['isLocked']['value'][0]
        method = valDict['passwordMethod']['value'][0]
        password = valDict[key]['value'][0]

        # If no method was given we do not have to save a password
        if not method:
            raise Exception("No password method was given!")
        else:
            manager = PasswordManager.get_instance()

            # Ask the password manager for a password-method that is
            # responsible for the given hashing-method.
            pwd_o = manager.get_method_by_method_type(method)
            if pwd_o:

                # Create a password hash and lock the account if necessary
                pwd_str = pwd_o.generate_password_hash(password, method)
                if is_locked:
                    pwd_str = pwd_o.lock_account(pwd_str)
                valDict[key]['value'] = [pwd_str]
            else:
                raise Exception("invalid password method given '%s'!" % method)

        return key, valDict
