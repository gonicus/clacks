# -*- coding: utf-8 -*-
"""
The *HTTPService* and the *HTTPDispatcher* are responsible for exposing
registered `WSGI <http://wsgi.org>`_ components to the world. While the
*HTTPService* is just providing the raw HTTP service, the *HTTPDispatcher*
is redirecting a path to a module.

-------
"""
import os
import thread
import logging
from zope.interface import implements
from webob import exc
from paste import httpserver

from clacks.common import Environment
from clacks.common.handler import IInterfaceHandler


class HTTPDispatcher(object):
    """
    The *HTTPDispatcher* can be used to register WSGI applications
    to a given path. It will inspect the path of an incoming request
    and decides which registered application it gets.

    Analyzing the path can be configured to detect a *subtree* match
    or an *exact* match. If you need subtree matches, just add the
    class variable ``http_subtree`` to the WSGI class and set it to
    *True*.
    """

    def __init__(self):
        self.__app = {}
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO')
        for app_path in sorted(self.__app, key=len, reverse=True):
            app = self.__app[app_path]

            if hasattr(app, "http_subtree") and path.startswith(app_path if app_path == "/" else app_path + "/"):
                return app.__call__(environ, start_response)
            elif path == app_path:
                return app.__call__(environ, start_response)

        # Nothing found
        self.log.debug('no resource %s registered!' % path)
        resp = exc.HTTPNotFound('no resource %s registered!' % path)
        return resp(environ, start_response)

    def register(self, path, app):
        self.log.debug("registering %s on %s" % (app.__class__.__name__, path))
        self.__app[path] = app

    def unregister(self, path):
        if path in self.__app:
            self.log.debug("unregistering %s" % path)
            del(self.__app[path])


class HTTPService(object):
    """
    Class to serve HTTP fragments to the interested client. It makes
    makes use of a couple of configuration flags provided by the clacks
    configuration files ``[http]`` section:

    ============== =============
    Key            Description
    ============== =============
    url            AMQP URL to connect to the broker
    id             User name to connect with
    key            Password to connect with
    command-worker Number of worker processes
    ============== =============

    Example::

        [http]
        host = node1.intranet.gonicus.de
        port = 8080
        sslpemfile = /etc/clacks/host.pem

    If you want to create a clacks agent module that is going to export
    functionality (i.e. static content or some RPC functionality) you
    can register such a component like this::

        >>> from clacks.common.components import PluginRegistry
        >>> class SomeTest(object):
        ...    http_subtree = True
        ...    path = '/test'
        ...
        ...    def __init__(self):
        ...        # Get http service instance
        ...        self.__http = PluginRegistry.getInstance('HTTPService')
        ...
        ...        # Register ourselves
        ...        self.__http.register(self.path, self)
        ...

    When *SomeTest* is instantiated, it will register itself to the *HTTPService* -
    and will be served when the *HTTPService* starts up.
    """
    implements(IInterfaceHandler)
    _priority_ = 10

    __register = {}

    def __init__(self):
        env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.info("initializing HTTP service provider")
        self.env = env
        self.srv = None
        self.ssl_pem = None
        self.app = None
        self.host = None
        self.scheme = None
        self.port = None

    def serve(self):
        """
        Start HTTP service thread.
        """
        self.app = HTTPDispatcher()

        self.host = self.env.config.get('http.host', default="localhost")
        self.port = self.env.config.get('http.port', default=8080)
        self.ssl_pem = self.env.config.get('http.sslpemfile', default=None)

        if self.ssl_pem:
            self.scheme = "https"
        else:
            self.scheme = "http"

        # Fetch server
        self.srv = httpserver.serve(self.app, self.host, self.port, start_loop=False, ssl_pem=self.ssl_pem)
        self.log.info("now serving on %s://%s:%s" % (self.scheme, self.host, self.port))
        thread.start_new_thread(self.srv.serve_forever, ())

        # Register all possible instances that have shown
        # interrest to be served
        for path, obj in self.__register.items():
            self.app.register(path, obj)

    def stop(self):
        """
        Stop HTTP service thread.
        """
        self.log.debug("shutting down HTTP service provider")
        self.srv.server_close()

    def register(self, path, obj):
        """
        Register the application *app* on path *path*.

        ================= ==========================
        Parameter         Description
        ================= ==========================
        path              Path part of an URL - i.e. '/rpc'
        app               WSGI application
        ================= ==========================
        """
        self.__register[path] = obj
