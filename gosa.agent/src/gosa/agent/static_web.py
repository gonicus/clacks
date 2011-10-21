# -*- coding: utf-8 -*-
import os
import mimetypes
import logging
from webob import Response, exc
from zope.interface import implements
from gosa.common.handler import IInterfaceHandler
from gosa.common import Environment
from gosa.common.components import PluginRegistry
from gosa.agent import __version__ as VERSION


class StaticWebService(object):
    implements(IInterfaceHandler)
    _priority_ = 11

    __proxy = {}

    def __init__(self):
        env = Environment.getInstance()
        self.env = env
        self.log = logging.getLogger(__name__)
        self.log.info("initializing static web service provider")
        self.path = self.env.config.get('http.path', default="/")

        self.__http = None

    def serve(self):
        # Get http service instance
        self.__http = PluginRegistry.getInstance('HTTPService')

        # Register ourselves
        self.__http.app.register(self.path, StaticApp())

        self.log.info("ready to process incoming requests")

    def stop(self):
        self.log.debug("shutting down static web service provider")
        self.__http.app.unregister(self.path)



class StaticApp(object):
    http_subtree = True

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.ident = "GOsa static web service (%s)" % VERSION
        self.root = self.env.config.get('http.root', default="/var/www")

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO')

        # Add index if we end with a /
        if path.endswith("/"):
            path = path + "index.html"

        path = os.path.join(self.root, os.path.normpath(path.lstrip("/")))

        res = self.make_response(path)
        return res(environ, start_response)

    def get_mimetype(self, filename):
        typ, encoding = mimetypes.guess_type(filename)
        #TODO: encoding
        return typ or 'application/octet-stream'

    def make_response(self, filename):
        # Check for existance and readability
        if not os.path.exists(filename):
            return exc.HTTPNotFound('Not found!')

        res = Response(content_type=self.get_mimetype(filename))
        res.app_iter = FileIterable(filename)
        res.content_length = os.path.getsize(filename)
        return res


class FileIterable(object):
    def __init__(self, filename, start=None, stop=None):
        self.filename = filename
        self.start = start
        self.stop = stop
    def __iter__(self):
        return FileIterator(self.filename, self.start, self.stop)
    def app_iter_range(self, start, stop):
        return self.__class__(self.filename, start, stop)


class FileIterator(object):
    chunk_size = 4096
    def __init__(self, filename, start, stop):
        self.filename = filename
        self.fileobj = open(self.filename, 'rb')
        if start:
            self.fileobj.seek(start)
        if stop is not None:
            self.length = stop - start
        else:
            self.length = None
    def __iter__(self):
        return self
    def next(self):
        if self.length is not None and self.length <= 0:
            raise StopIteration
        chunk = self.fileobj.read(self.chunk_size)
        if not chunk:
            raise StopIteration
        if self.length is not None:
            self.length -= len(chunk)
            if self.length < 0:
                # Chop off the extra:
                chunk = chunk[:self.length]
        return chunk
