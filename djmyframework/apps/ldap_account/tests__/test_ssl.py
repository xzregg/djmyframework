# -*- coding: utf-8 -*-
# @Time    : 2021-03-31 17:10
# @Author  : xzr
# @File    : test_ssl
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    : 

from twisted.internet import ssl, reactor
from twisted.internet.protocol import Factory, Protocol

class Echo(Protocol):
    def dataReceived(self, data):
        """As soon as any data is received, write it back."""
        self.transport.write(data)


factory = Factory()
factory.protocol = Echo
reactor.listenSSL(8001, factory,
                  ssl.DefaultOpenSSLContextFactory(
        '../keys/server.key', '../keys/server.crt'))
reactor.run()