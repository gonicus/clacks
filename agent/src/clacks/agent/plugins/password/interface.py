
class PasswordMethod(object):
    """
    The interface all password-methods should use.
    """
    hash_name = None

    def is_locked(self, hash_value):
        """
        Checks whether the account is locked or not.
        """
        raise NotImplementedError("password method is not capable of locking accounts")

    def lock_account(self, hash_value):
        """
        Locks the given account.
        """
        raise NotImplementedError("password method is not capable of locking accounts")

    def unlock_account(self, hash_value):
        """
        Unlocks the given account.
        """
        raise NotImplementedError("password method is not capable of locking accounts")

    def is_configurable(self):
        """
        Returns whether this password method is configurable or not
        """
        return False

    def get_hash_names(self):
        """
        Returns a list of hashing-mechanisms that are supported by the password method.
        """
        return [self.hash_name]

    def is_responsible_for_password_hash(self, password_hash):
        """
        Checks whether this class is responsilbe for this kind of password hashes of not.
        """
        raise NotImplementedError("is_responsible_for_password_hash method is not implemented")

    def generate_password_hash(self, new_password, method=None):
        """
        Generates a password hash for the given password and method
        """
        raise NotImplementedError("is_responsible_for_password_hash method is not implemented")
