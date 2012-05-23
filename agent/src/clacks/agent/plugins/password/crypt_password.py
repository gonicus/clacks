from clacks.agent.plugins.password.interface import PasswordMethod
import re
import crypt
import random
import string
import re

class PasswordMethodCrypt(PasswordMethod):
    hash_name = "CRYPT"

    def is_responsible_for_password_hash(self, password_hash):
        if re.match("^\{%s\}" % self.hash_name, password_hash):
            return True
        return False

    def detect_hash_method(self, password_hash):
        if not self.is_responsible_for_password_hash(password_hash):
            return None

        password_hash = re.sub('^{[^}]+}!?', '', password_hash)
        if re.match('^[a-zA-Z0-9.\/][a-zA-Z0-9.\/]', password_hash):
            return "crypt/standard-des"

        if re.match('^_[a-zA-Z0-9.\/]', password_hash):
            return "crypt/enhanced-des"

        if re.match('^\$1\$', password_hash):
            return "crypt/md5"

        if re.match('^(\$2\$|\$2a\$)', password_hash):
            return "crypt/blowfish"

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

        return u"{%s}%s" % (self.hash_name, crypt.crypt(new_password, salt))
