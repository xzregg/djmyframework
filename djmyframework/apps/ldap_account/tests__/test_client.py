# -*- coding: utf-8 -*-
# @Time    : 2021-03-31 15:45
# @Author  : xzr
# @File    : test_client
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    : 

import sys

from twisted.internet import defer
from twisted.internet.endpoints import clientFromString, connectProtocol
from twisted.internet.task import react
from ldaptor.protocols.ldap.ldapclient import LDAPClient
from ldaptor.protocols.ldap.ldapsyntax import LDAPEntry


@defer.inlineCallbacks
def onConnect(client):
    # The following arguments may be also specified as unicode strings
    # but it is recommended to use byte strings for ldaptor objects
    basedn = b"dc=ldap,dc=com"
    binddn = b"cn=ldap,ou=user,dc=ldap,dc=com"
    bindpw = b"123456"
    query = b"(cn=test)"
    try:
        yield client.bind(binddn, bindpw)
    except Exception as ex:
        print(ex)
        raise
    o = LDAPEntry(client, basedn)
    results = yield o.search(filterText=query)
    for entry in results:
        print(entry.getLDIF())


def onError(err):
    err.printDetailedTraceback(file=sys.stderr)


def main(reactor):
    endpoint_str = "tcp:host=127.0.0.1:port=13891"
    e = clientFromString(reactor, endpoint_str)
    d = connectProtocol(e, LDAPClient())
    d.addCallback(onConnect)
    d.addErrback(onError)
    return d


if __name__ == '__main__':
    react(main)