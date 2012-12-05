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

"""
The configuration module is the central place where the clacks configuration
can be queried. Using the configuration module requires the presence of the
clacks configuration file - commonly ``/etc/clacks/config`` and the subdirectory
``/etc/clacks/config.d``. All these configurations will be merged into one
'virtual' configuration so that certain packages can provide their own config
file without knowing how to read it.

Additionally to reading the configuration file, it merges that information
with potential command line parameters.

Here is an example on how to use the common module::

    >>> from clacks.common import Environment
    >>> cfg = Environment.getInstance().config
    >>> cfg.get('core.id')
    amqp

If no configuration is present, the system will raise a
:class:`clacks.common.config.ConfigNoFile` exception.

-----------
"""
import os
import re
import platform
import ConfigParser
import logging.config
import getpass
from argparse import ArgumentParser
from clacks.common import __version__ as VERSION

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


# Only import pwd/grp stuff if we're not on windows
if platform.system() != "Windows":
    import pwd
    import grp


class ConfigNoFile(Exception):
    """
    Exception to inform about non existing or not accessible
    configuration files.
    """
    pass


class Config(object):
    """
    Construct a new Config object using the provided configuration file
    and parse the ``sys.argv`` information.

    ========= ============
    Parameter Description
    ========= ============
    config    Path to the configuration file.
    noargs    Don't parse ``sys.argv`` information
    ========= ============
    """
    __registry = {'core': {
                    'pidfile': '/var/run/clacks/clacks.pid',
                    'profile': 0,
                    'umask': 0o002,
                }
            }
    __configKeys = None

    def __init__(self, config=None, noargs=False):
        if not config:
            config = os.environ.get('CLACKS_CONFIG_DIR') or "/etc/clacks"

        # Load default user name for config parsing
        self.__registry['core']['config'] = config
        self.__noargs = noargs

        # Load file configuration
        if not self.__noargs:
            self.__parseCmdOptions()
        self.__parseCfgOptions()

        # Overload with command line options
        if not self.__noargs:
            self.__parseCmdOptions()

        if platform.system() != "Windows":
            user = getpass.getuser()
            userHome = pwd.getpwnam(user).pw_dir
            group = grp.getgrgid(pwd.getpwnam(user).pw_gid).gr_name

            self.__registry['core']['user'] = user
            self.__registry['core']['group'] = group

    def __parseCmdOptions(self):
        parser = ArgumentParser(usage="%(prog)s - the clacks core daemon")
        parser.add_argument("--version", action='version', version=VERSION)

        parser.add_argument("-c", "--config", dest="config",
                          default=os.environ.get('CLACKS_CONFIG_DIR') or "/etc/clacks",
                          help="read configuration from FILE [%(default)s]",
                          metavar="FILE")
        parser.add_argument("--url", dest="url",
                          help="AMQP broker URL",
                          metavar="URL")
        parser.add_argument("--profile", action="store_true", dest="profile",
                          help="write profiling information [%(default)s]")

        options = parser.parse_args()

        items = options.__dict__
        self.__registry['core'].update(dict([(k, items[k]) for k in items if items[k] != None]))
        if self.get("core.url", None):
            self.__registry['amqp'] = {'url': self.get("core.url")}
            del self.__registry['core']['url']

    def getBaseDir(self):
        return self.__registry['core']['config']

    def getSections(self):
        """
        Return the list of available sections of the ini file. There should be at
        least 'core' available.

        ``Return``: list of sections
        """
        return self.__registry.keys()

    def getOptions(self, section):
        """
        Return the list of provided option names in the specified section of the
        ini file.

        ========= ============
        Parameter Description
        ========= ============
        str       section name in the ini file
        ========= ============

        ``Return``: list of options
        """
        return self.__registry[section.lower()]

    def get(self, path, default=None):
        """
        *get* allows dot-separated access to the configuration structure.
        If the desired value is not defined, you can specify a default
        value.

        For example, if you want to access the *id* option located
        in the section *[core]*, the path is:

            core.id

        ========= ============
        Parameter Description
        ========= ============
        path      dot-separated path to the configuration option
        default   default value if the desired option is not set
        ========= ============

        ``Return``: value or default
        """
        tmp = self.__registry
        try:
            for pos in path.split("."):
                tmp = tmp[pos.lower()]
            return tmp

        except KeyError:
            pass

        return default

    def __getCfgFiles(self, cdir):
        conf = re.compile(r"^[a-z0-9_.-]+\.conf$", re.IGNORECASE)
        try:
            return [os.path.join(cdir, cfile)
                for cfile in os.listdir(cdir)
                if os.path.isfile(os.path.join(cdir, cfile)) and conf.match(cfile)]
        except OSError:
            return []

    def __parseCfgOptions(self):
        # Is there a configuration available?
        configDir = self.get('core.config')
        configFiles = self.__getCfgFiles(os.path.join(configDir, "config.d"))
        configFiles.insert(0, os.path.join(configDir, "config"))

        config = ConfigParser.RawConfigParser()
        filesRead = config.read(configFiles)

        # Bail out if there's no configuration file
        if not filesRead:
            raise ConfigNoFile("No usable configuration file (%s/config) found!" % configDir)

        # Walk thru core configuration values and push them into the registry
        for section in config.sections():
            if not section in self.__registry:
                self.__registry[section] = {}
            self.__registry[section].update(config.items(section))

        # Initialize the logging module on the fly
        try:
            tmp = StringIO()
            config.write(tmp)
            tmp2 = StringIO(tmp.getvalue())
            logging.config.fileConfig(tmp2)

        except ConfigParser.NoSectionError:
            logging.basicConfig(level=logging.ERROR, format='%(asctime)s (%(levelname)s): %(message)s')
