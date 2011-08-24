# -*- coding: utf-8 -*-
import urllib
import hashlib

from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.utils import N_
from gosa.common import Environment

class GravatarUtils(Plugin):
    """
    Utility class that contains methods needed to retrieve gravatar
    URLs.
    """
    _target_ = 'gravatar'

    def __init__(self):
        env = Environment.getInstance()
        self.env = env

    @Command(__help__=N_("Generate samba lm:nt hash combination "+
        "from the supplied password."))
    def getGravatarURL(self, mail, size=40, url="http://www.gonicus.de"):
        """
        TODO
        """
        gravatar_url = "http://www.gravatar.com/avatar.php?"
        gravatar_url += urllib.urlencode({
            'gravatar_id': hashlib.md5(mail.lower()).hexdigest(),
            'default': url,
            'size': str(size)})
        return gravatar_url
