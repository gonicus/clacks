from twisted.internet import ssl, reactor
from twisted.internet.protocol import Factory, Protocol
from twisted.web.wsgi import WSGIResource
from twisted.web import server

def application(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/plain')])
    return ['Hello, world!']

if __name__ == '__main__':
    factory = Factory()
    resource = WSGIResource(reactor, reactor.getThreadPool(), application)
    reactor.listenSSL(8000, server.Site(resource), ssl.DefaultOpenSSLContextFactory('key.key', 'key.cert'))
    reactor.run()

