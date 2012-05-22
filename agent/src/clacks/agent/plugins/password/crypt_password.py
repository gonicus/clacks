from clacks.agent.plugins.password.interface import PasswordMethod
import re
import crypt
import random
import string

class PasswordMethodCrypt(PasswordMethod):
    hash_name = "CRYPT"

    def is_responsible_for_password_hash(self, password_hash):
        if re.match("^\{%s\}" % self.hash_name, password_hash):
            return True
        return False

    def detect_method(self, password_hash):
        return None

    def is_locked(self, password_hash):
        return re.match("\{[^\}]*\}!", password_hash) != None

    def lock_account(self, password_hash):
        return re.sub("\{([^\}]*)\}!?", "{\\1}!", password_hash)

    def unlock_account(self, password_hash):
        return re.sub("\{([^\}]*)\}!?", "{\\1}", password_hash)

    def get_hash_names(self):
        return ["crypt/standard-des", "crypt/enhanced-des", "crypt/md5", "crypt/blowfish"]

    def generate_password_hash(self, new_password, method=None):

        salt = ""
        if method == "crypt/standard-des":
            for i in range(2):
                salt += random.choice(string.letters + string.digits)

        if method == "crypt/enhanced-des":
            salt = "_"
            for i in range(8):
                salt += random.choice(string.letters + string.digits)

        if method == "crypt/md5":
            salt = "$1$"
            for i in range(8):
                salt += random.choice(string.letters + string.digits)
            salt += "$"

        if method == "crypt/blowfish":
            salt = "$2a$07$";
            CRYPT_SALT_LENGTH = 8 #TODO: ??
            for i in range(CRYPT_SALT_LENGTH):
                salt += random.choice(string.letters + string.digits)
            salt += "$"

        return "{%s}%s" % (self.hash_name, crypt.crypt(new_password, salt))
