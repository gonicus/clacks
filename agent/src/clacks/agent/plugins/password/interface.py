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
from clacks.common.error import ClacksErrorHandler as C


class PasswordMethod(object):
    """
    The interface all password-methods should use.
    """
    hash_name = None

    def isLockable(self, hash_value):
        """
        Tells whether the password hash can be locked or not
        """
        return False

    def isUnlockable(self, hash_value):
        """
        Tells whether the password hash can be unlocked or not
        """
        return False

    def is_locked(self, hash_value):
        """
        Checks whether the account is locked or not.
        """
        raise NotImplementedError(C.make_error('NOT_IMPLEMENTED', method="is_locked"))

    def lock_account(self, hash_value):
        """
        Locks the given account.
        """
        raise NotImplementedError(C.make_error('NOT_IMPLEMENTED', method="lock_account"))

    def unlock_account(self, hash_value):
        """
        Unlocks the given account.
        """
        raise NotImplementedError(C.make_error('NOT_IMPLEMENTED', method="unlock_account"))

    def get_hash_names(self):
        """
        Returns a list of hashing-mechanisms that are supported by the password method.
        """
        return [self.hash_name]

    def is_responsible_for_password_hash(self, password_hash):
        """
        Checks whether this class is responsilbe for this kind of password hashes of not.
        """
        raise NotImplementedError(C.make_error('NOT_IMPLEMENTED', method="is_responsible_for_password_hash"))

    def generate_password_hash(self, new_password, method=None):
        """
        Generates a password hash for the given password and method
        """
        raise NotImplementedError(C.make_error('NOT_IMPLEMENTED', method="generate_password_hash"))
