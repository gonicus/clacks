# -*- coding: utf-8 -*-
"""
The configuration module is the central place where the GOsa configuration
can be queried. Using the configuration module requires the presence of the
GOsa configuration file - commonly ``/etc/gosa/config`` and the subdirectory
``/etc/gosa/config.d``. All these configurations will be merged into one
'virtual' configuration so that certain packages can provide their own config
file without knowing how to read it.

Additionally to reading the configuration file, it merges that information
with potential command line parameters.

Here is an example on how to use the common module::

    >>> from gosa.common import Environment
    >>> cfg = Environment.getInstance().config
    >>> cfg.get('core.id')
    amqp

If no configuration is present, the system will raise a
:class:`gosa.common.config.ConfigNoFile` exception.

-----------
"""
import os
import re
import platform
import StringIO
import ConfigParser
import logging.config
from argparse import ArgumentParser
from gosa.common import __version__ as VERSION

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
                    'foreground': False,
                    'pidfile': '/var/run/gosa/gosa.pid',
                    'profile': 0,
                    'umask': 0o002,
                }
            }
    __configKeys = None

    def __init__(self,  config="/etc/gosa/config",  noargs=False):
        # Load default user name for config parsing
        self.__registry['core']['config'] = config
        self.__noargs = noargs
        user = 'gosa'
        group = 'gosa'
        userHome = '/var/lib/gosa'

        if platform.system() != "Windows":
            try:
                userHome = pwd.getpwnam(user).pw_dir
                group = grp.getgrgid(pwd.getpwnam(user).pw_gid).gr_name
            except KeyError:
                pass

            self.__registry['core']['user'] = user
            self.__registry['core']['group'] = group
            self.__registry['core']['workdir'] = userHome

        # Load file configuration
        if not self.__noargs:
            self.__parseCmdOptions()
        self.__parseCfgOptions()

        # Overload with command line options
        if not self.__noargs:
            self.__parseCmdOptions()

    def __parseCmdOptions(self):
        parser = ArgumentParser(usage="%(prog)s - the GOsa core daemon")
        parser.add_argument("--version", action='version', version=VERSION)

        parser.add_argument("-c", "--config", dest="config",
                          default="/etc/gosa/config",
                          help="read configuration from FILE [%(default)s]",
                          metavar="FILE")
        parser.add_argument("-f", action="store_true", dest="foreground",
                          help="run daemon in foreground [%(default)s]")
        parser.add_argument("-u", "--user", dest="user",
                          help="run daemon as USER [%(default)s]",
                          metavar="USER")
        parser.add_argument("-g", "--group", dest="group",
                          help="run daemon as GROUP [%(default)s]",
                          metavar="GROUP")
        parser.add_argument("-p", "--pid-file", dest="pidfile",
                          help="store PID information into FILE [%(default)s]",
                          metavar="FILE")
        parser.add_argument("--profile", action="store_true", dest="profile",
                          help="write profiling information (only if daemon runs in foreground mode [%(default)s]")

        group = parser.add_argument_group("Advanced options")
        group.add_argument("--umask", dest="umask",
                          help="run daemon with UMASK [%(default)s]",
                          metavar="UMASK")
        group.add_argument("--workdir", dest="workdir",
                          help="change directory to DIR after starting up [%(default)s]",
                          metavar="DIR")

        options = parser.parse_args()

        items = options.__dict__
        self.__registry['core'].update(dict([(k, items[k]) for k in items if items[k] != None]))

    def getBaseDir(self):
        bd = os.path.dirname(self.__registry['core']['config'])
        if bd == self.__registry['core']['config']:
            return ""

        return bd

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
        configFile = self.get('core.config')
        configFiles = self.__getCfgFiles(configFile + ".d")
        configFiles.insert(0, configFile)

        config = ConfigParser.RawConfigParser()
        filesRead = config.read(configFiles)

        # Bail out if there's no configuration file
        if not filesRead:
            raise ConfigNoFile("No usable configuration file (%s) found!" % configFile)

        # Walk thru core configuration values and push them into the registry
        for section in config.sections():
            if not section in self.__registry:
                self.__registry[section] = {}
            self.__registry[section].update(config.items(section))

        # Initialize the logging module on the fly
        try:
            tmp = StringIO.StringIO()
            config.write(tmp)
            tmp2 = StringIO.StringIO(tmp.getvalue())
            logging.config.fileConfig(tmp2)

        except ConfigParser.NoSectionError:
            logging.basicConfig(level=logging.ERROR, format='%(asctime)s (%(levelname)s): %(message)s')
