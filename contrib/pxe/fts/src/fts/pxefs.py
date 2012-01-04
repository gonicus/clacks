# -*- coding: utf-8 -*-
import os
import re
import stat
import fuse
import syslog
import argparse
import ConfigParser
import pkg_resources
from time import time
from fts.filestat import FileStat
from fts.plugins.interface import BootPlugin


macaddress = re.compile("^[0-9a-f]{1,2}-[0-9a-f]{1,2}-[0-9a-f]{1,2}-[0-9a-f]{1,2}-[0-9a-f]{1,2}-[0-9a-f]{1,2}$", re.IGNORECASE)


class PXEfs(fuse.Fuse):

    def __init__(self, *args, **kw):
        # Load specified configuration file
        parser = argparse.ArgumentParser(
            description="""This services provides a user space filesystem overlay for dynamically
generated PXE configurations. It takes a static directory and provides the
files from that directory on a newly mounted path - which gets filtered by
a set of plugins that can provide drop in configurations for certain MAC
addresses.""",
            prog='fts',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--config', '-c',
            metavar='FILE',
            help='path to the configuration file', default="/etc/fts/config")

        cli_opts = parser.parse_args()
        self.load_config(cli_opts.config)

        # Sanity checks
        if not os.access(self.cfg_path, os.F_OK):
            syslog.syslog(syslog.LOG_ERR, "base path '%s' does not exist" % self.cfg_path)
            exit(1)
        if not os.access(self.static_path, os.F_OK):
            syslog.syslog(syslog.LOG_ERR, "static path '%s' does not exist" % self.static_path)
            exit(1)

        # Inject mount point
        fa = fuse.FuseArgs()
        fa.mountpoint = self.cfg_path
        kw['fuse_args'] = fa

        fuse.Fuse.__init__(self, *args, **kw)
        self.root = os.sep
        self.filesystem = {
            self.root : {
                "content": "",
            }
        }
        self.positive_cache_timeout = 10

        # Load all registered boot methods
        self.boot_method_reg = {}
        for entry in pkg_resources.iter_entry_points("fts.plugin"):
            module = entry.load()
            #TODO: check for parent -> BootPlugin
            print issubclass(module, BootPlugin)
            self.boot_method_reg[module.__name__] = module()
            syslog.syslog(syslog.LOG_INFO, "boot plugin '%s' included" % module.getInfo())

    def load_config(self, cfg):
        config = ConfigParser.SafeConfigParser({
            'static-path': '/tftpboot/pxelinux.static',
            'path': '/tftpboot/pxelinux.cfg'})
        config.read(cfg)

        try:
            config.get('pxe', 'static-path')

        except ConfigParser.NoSectionError:
            config.add_section('pxe')

        self.static_path = config.get('pxe', 'static-path')
        self.cfg_path = config.get('pxe', 'path')

    def fsdestroy(self, **args):
        syslog.syslog(syslog.LOG_INFO, "fts is terminating")

    def getattr(self, path):
        result = FileStat()
        if path == self.root:
            pass
        elif os.path.exists(os.sep.join((self.static_path, path))):
            result = os.stat(os.sep.join((self.static_path, path)))
        else:
            result.st_mode = stat.S_IFREG | 0666
            result.st_nlink = 1
            result.st_size = self.getSize(path)
        return result

    def read(self, path, size, offset):
        return self.getContent(path, size, offset)

    def readdir(self, path, offset):
        direntries=[ '.', '..' ]
        if os.path.exists(os.sep.join((self.static_path, path))):
            direntries.extend(os.listdir(os.sep.join((self.static_path, path))))
        elif self.filesystem[path].keys():
            direntries.extend(self.filesystem[path].keys())
        for directory in direntries:
            yield fuse.Direntry(directory)

    def getContent(self, path, size, offset):
        result = ""
        if os.path.exists(os.sep.join((self.static_path, path))):
            with open(os.sep.join((self.static_path, path))) as f:
                f.seek(offset)
                result = f.read(size)
        elif macaddress.match(path[4:]):
            result = self.getBootParams(path)[offset:offset+size]
        elif path.lstrip(os.sep) in self.filesystem[self.root].keys():
            result = str(self.filesystem[self.root][path.lstrip(os.sep)]['content'])[offset:offset+size]
        return result

    def getSize(self, path):
        result = 0
        if os.path.exists(os.sep.join((self.static_path, path))):
            result = os.path.getsize(os.sep.join((self.static_path, path)))
        elif macaddress.match(path[4:]):
            result = len(self.getBootParams(path))
        elif path.lstrip(os.sep) in self.filesystem[self.root].keys():
            result = len(str(self.filesystem[self.root][path.lstrip(os.sep)]['content']))
        return result

    def getBootParams(self, path):
        if not path in self.filesystem[self.root] \
            or not 'timestamp' in self.filesystem[self.root][path] \
            or self.filesystem[self.root][path]['timestamp'] < int(time()) - int(self.positive_cache_timeout):
            self.filesystem[self.root][path] = {}

            # Iterate over known modules, first match wins
            for method in self.boot_method_reg:
                syslog.syslog(syslog.LOG_DEBUG, "checking boot method '%s'" % method)

                # Need to transform /01-00-00-00-00-00-00 into 00:00:00:00:00:00
                content = self.boot_method_reg[method].getBootParams(path[4:].replace('-', ':'))
                if content is not None:
                    syslog.syslog(syslog.LOG_DEBUG, "found relevant information: " % content)
                    self.filesystem[self.root][path]['content'] = str(content)
                    self.filesystem[self.root][path]['timestamp'] = time()
                    break

        return self.filesystem[self.root][path]['content'] if 'content' in self.filesystem[self.root][path] else None
