# -*- coding: utf-8 -*-

import os
import sys

from twisted.internet.endpoints import serverFromString

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

from twisted.application import service
from twisted.internet.protocol import ServerFactory
from twisted.python.components import registerAdapter
from twisted.python import log
from ldaptor.interfaces import IConnectedLDAPEntry
from ldaptor.protocols.ldap.ldapserver import LDAPServer
import shutil
from ldaptor import ldiftree
from .settings import LDAP_ACCOUNT_SERVER_PORT
from framework.utils import single_process
from framework.apps import get_app_path
from .settings import DBPATH
from twisted.internet import ssl, reactor

APP_PATH = get_app_path('ldap_account')


class LDAPServerFactory(ServerFactory):
    protocol = LDAPServer

    def __init__(self, root):
        self.root = root

    def buildProtocol(self, addr):
        proto = self.protocol()
        proto.debug = self.debug
        proto.factory = self
        return proto


def get_db_path():
    TPL_DBPATH = os.path.join(APP_PATH, 'ldiftree')
    tmp_db_path = DBPATH

    if not os.path.exists(tmp_db_path):
        shutil.rmtree(tmp_db_path, ignore_errors=True)
        shutil.copytree(TPL_DBPATH, tmp_db_path)
    return tmp_db_path


def get_db():
    db = ldiftree.LDIFTreeEntry(get_db_path())
    return db


@single_process.SingleProcessDeco()
def run_ldap_server(port=LDAP_ACCOUNT_SERVER_PORT, use_ssl=False):
    log.startLogging(sys.stderr)
    # We initialize our tree

    # When the LDAP Server protocol wants to manipulate the DIT, it invokes
    # `root = interfaces.IConnectedLDAPEntry(self.factory)` to get the root
    # of the DIT.  The factory that creates the protocol must therefore
    # be adapted to the IConnectedLDAPEntry interface.
    registerAdapter(
            # lambda x: get_db(),
            lambda x: x.root,

            LDAPServerFactory,
            IConnectedLDAPEntry)

    factory = LDAPServerFactory(get_db())
    factory.debug = True
    application = service.Application("ldaptor-server")
    myService = service.IServiceCollection(application)

    if use_ssl:
        print('use ssl')
        reactor.listenSSL(port, factory,
                          ssl.DefaultOpenSSLContextFactory(
                                  os.path.join(APP_PATH, 'keys/server.key'), os.path.join(APP_PATH, 'keys/server.crt')))

    else:
        serverEndpointStr = "tcp:{0}".format(port)
        e = serverFromString(reactor, serverEndpointStr)
        e.listen(factory)
    reactor.run()


if __name__ == '__main__':
    run_ldap_server()
