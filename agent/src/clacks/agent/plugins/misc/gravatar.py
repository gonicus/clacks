# -*- coding: utf-8 -*-
import urllib
import hashlib

from clacks.common.components import Command
from clacks.common.components import Plugin
from clacks.common.utils import N_
from clacks.common import Environment


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
        Generate the gravatar URL to be used for user pictures on
        demand.

        ========= ======================================
        Parameter Description
        ========= ======================================
        mail      Gravatar's mail address
        size      desired image size
        url       Clickable URL
        ========= ======================================

        ``Return:`` Image URL
        """
        gravatar_url = "http://www.gravatar.com/avatar.php?"
        gravatar_url += urllib.urlencode({
            'gravatar_id': hashlib.md5(mail.lower()).hexdigest(),
            'default': url,
            'size': str(size)})
        return gravatar_url
