import sys
from twisted.internet import reactor, ssl
from twisted.python import log
from autobahn.websocket import WebSocketServerFactory, WebSocketServerProtocol

import pprint

class BroadcastServerProtocol(WebSocketServerProtocol):

   def onOpen(self):
      self.factory.register(self)

   def onMessage(self, msg, binary):
      pprint.pprint(self.http_headers)
      if not binary:
         self.factory.broadcast("received message '%s' from %s" % (msg, self.peerstr))

   def connectionLost(self, reason):
      WebSocketServerProtocol.connectionLost(self, reason)
      self.factory.unregister(self)


class BroadcastServerFactory(WebSocketServerFactory):

   protocol = BroadcastServerProtocol

   def __init__(self):
      WebSocketServerFactory.__init__(self)
      self.clients = []
      self.tickcount = 0
      self.tick()

   def tick(self):
      self.tickcount += 1
      #self.broadcast("tick %d" % self.tickcount)
      #reactor.callLater(1, self.tick)

   def register(self, client):
      if not client in self.clients:
         print "registered client " + client.peerstr
         if 'Cookie' in client.http_headers:
            print "Got Cookie:",client.http_headers['Cookie']
         else:
            print "No Cookie!!"

   def unregister(self, client):
      if client in self.clients:
         print "unregistered client " + client.peerstr
         self.clients.remove(client)

   def broadcast(self, msg):
      print "broadcasting message '%s' .." % msg
      for c in self.clients:
         print "send to " + c.peerstr
         c.sendMessage(msg)


if __name__ == '__main__':

   log.startLogging(sys.stdout)
   factory = BroadcastServerFactory()
   #reactor.listenTCP(9000, factory)
   reactor.listenSSL(9000, factory, ssl.DefaultOpenSSLContextFactory('key.key', 'key.cert'))
   reactor.run()
