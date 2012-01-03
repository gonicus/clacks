#!/usr/bin/env python
# -*- coding: utf-8 -*-
import errno
import os
import re
import stat
import daemon
import signal
import lockfile
import pkg_resources
from time import time
from clacks.common import Environment

try:
    import _find_fuse_parts
except ImportError:
    pass

import fuse

server = None

fuse.fuse_python_api = (0, 2)

if not hasattr(fuse, '__version__'):
    raise RuntimeError, \
        "your fuse-py doesn't know of fuse.__version__, probably it's too old."

fuse.feature_assert('stateful_files', 'has_init')
macaddress = re.compile("^[0-9a-f]{1,2}-[0-9a-f]{1,2}-[0-9a-f]{1,2}-[0-9a-f]{1,2}-[0-9a-f]{1,2}-[0-9a-f]{1,2}$", re.IGNORECASE)


def getDepth(path):
    """
    Return the depth of a given path, zero-based from root ('/')
    """
    if path=='/':
        return 0
    else:
        return path.count('/')


def getParts(path):
    """
    Return the slash-separated parts of a given path as a list
    """
    if path=='/':
        return [['/']]
    else:
        return path.split('/')


class FileStat(fuse.Stat):

    def __init__(self):
        self.st_mode = stat.S_IFDIR | 0755
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 2
        self.st_uid = os.getuid()
        self.st_gid = os.getgid()
        self.st_size = 4096
        self.st_atime = int(time())
        self.st_mtime = self.st_atime
        self.st_ctime = self.st_atime


class PxeFS(fuse.Fuse):

    def __init__(self, *args, **kw):
        Environment.config = "/etc/fts/config"
        Environment.noargs = True
        self.env = Environment.getInstance()
        self.static = self.env.config.get('pxe.static-path', '/tftpboot/pxelinux.static')
        self.cfg_path = self.env.config.get('pxe.path', '/tftpboot/pxelinux.cfg')

        # Sanity checks
        if not os.access(self.cfg_path, os.F_OK):
            self.env.log.error("base path '{path}' does not exist".format(path=self.cfg_path))
            exit(1)
        if not os.access(self.static, os.F_OK):
            self.env.log.error("static path '{path}' does not exist".format(path=static_path))
            exit(1)

        # Inject mount point and foreground mode
        fa = fuse.FuseArgs()
        fa.mountpoint = self.cfg_path
        fa.setmod('foreground')
        kw['fuse_args'] = fa

        fuse.Fuse.__init__(self, *args, **kw)
        self.root = os.sep
        self.filesystem = {
            self.root : {
                "content": "",
            }
        }
        self.positive_cache_timeout = 10

        # Load all boot methods
        self.boot_method_reg = {}
        for entry in pkg_resources.iter_entry_points("fts.methods"):
            module = entry.load()
            self.env.log.info("boot method {method} included ".format(method=module.__name__))
            self.boot_method_reg[module.__name__] = module

    def getattr(self, path):
        result = FileStat()
        if path == self.root:
            pass
        elif os.path.exists(os.sep.join((self.static, path))):
            result = os.stat(os.sep.join((self.static, path)))
        else:
            result.st_mode = stat.S_IFREG | 0666
            result.st_nlink = 1
            result.st_size = self.getSize(path)
        return result

    def read(self, path, size, offset):
        return self.getContent(path, size, offset)

    def readdir(self, path, offset):
        direntries=[ '.', '..' ]
        if os.path.exists(os.sep.join((self.static, path))):
            direntries.extend(os.listdir(os.sep.join((self.static, path))))
        elif self.filesystem[path].keys():
            direntries.extend(self.filesystem[path].keys())
        for directory in direntries:
            yield fuse.Direntry(directory)

    def getContent(self, path, size, offset):
        result = ""
        if os.path.exists(os.sep.join((self.static, path))):
            with open(os.sep.join((self.static, path))) as f:
                f.seek(offset)
                result = f.read(size)
        elif macaddress.match(path[4:]):
            result = self.getBootParams(path)[offset:offset+size]
        elif path.lstrip(os.sep) in self.filesystem[self.root].keys():
            result = str(self.filesystem[self.root][path.lstrip(os.sep)]['content'])[offset:offset+size]
        return result

    def getSize(self, path):
        result = 0
        if os.path.exists(os.sep.join((self.static, path))):
            result = os.path.getsize(os.sep.join((self.static, path)))
        elif macaddress.match(path[4:]):
            result = len(self.getBootParams(path))
        elif path.lstrip(os.sep) in self.filesystem[self.root].keys():
            result = len(str(self.filesystem[self.root][path.lstrip(os.sep)]['content']))
        return result

    def getBootParams(self, path):
        if not path in self.filesystem[self.root] \
            or not timestamp in self.filesystem[self.root][path] \
            or self.filesystem[self.root][path]['timestamp'] < int(time()) - int(self.positive_cache_timeout):
            self.filesystem[self.root][path] = {}

            # Iterate over known modules, first match wins
            for method in self.boot_method_reg:
                self.env.log.debug("Calling boot method {method}".format(method=method))
                try:
                    # Need to transform /01-00-00-00-00-00-00 into 00:00:00:00:00:00
                    content = self.boot_method_reg[method]().getBootParams(path[4:].replace('-', ':'))
                    if content is not None:
                        print "Found content", content
                        self.filesystem[self.root][path]['content'] = str(content)
                        self.filesystem[self.root][path]['timestamp'] = time()
                        break
                except:
                    continue
        return self.filesystem[self.root][path]['content'] if 'content' in self.filesystem[self.root][path] else None


def main():
    global server

    usage = "\nTFTP supplicant: provide pxelinux configuration files based on external state information.\n" + fuse.Fuse.fusage

    server = PxeFS(version="%prog " + fuse.__version__,
                 usage=usage,
                 dash_s_do='setsingle')

    # Disable multithreading: if you want to use it, protect all method of
    # XmlFile class with locks, in order to prevent race conditions
    server.multithreaded = False
    server.parser.add_option(mountopt="root", metavar="PATH", default=os.sep, help="mirror filesystem from under PATH [default: %default]")
    server.parse(values=server, errex=1)

    try:
        if server.fuse_args.mount_expected():
            os.chdir(server.root)
    except OSError:
        print >> sys.stderr, "can't enter root of underlying filesystem"
        sys.exit(1)

    context = daemon.DaemonContext(working_directory='/var/lib/fts',
        umask=0o002,
        pidfile=lockfile.FileLock('/var/run/fts.pid'))

    #context.signal_map = {
    #    signal.SIGTERM: shutdown,
    #    signal.SIGHUP: 'terminate',
    #}

    with context:
        server.main()


if __name__ == '__main__':
    main()
