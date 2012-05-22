
class PasswordMethod(object):

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

    def is_configurable():
        return False

    def get_hash_names(self):
        return [self.hash_name]

    def is_responsible_for_password_hash(self, password_hash):
        raise NotImplementedError("is_responsible_for_password_hash method is not implemented")

    def generate_password_hash(new_password, method=None):
        raise NotImplementedError("is_responsible_for_password_hash method is not implemented")
