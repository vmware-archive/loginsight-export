import logging
import sys
import requests
import pytest
import warnings
import requests_mock
import socket
from collections import namedtuple

from mock_loginsight_server import MockedConnection
from loginsightexport.uidriver import Connection, Credentials, TechPreviewWarning


usemockserver = True
useliveserver = True
useinternet = False


warnings.simplefilter('default')
warnings.filterwarnings("ignore", category=TechPreviewWarning)
warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

socket.setdefaulttimeout(1)
ConnectionContainer = namedtuple("Connections", ["clazz", "hostname", "goodcredentials", "verify"])

try:
    from CREDENTIALS import hostname, username, provider, password
    live_server = ConnectionContainer(Connection, hostname, Credentials(username, password, provider), False)
except ImportError:
    live_server = None


def pytest_generate_tests(metafunc):
    """Called by pytest to parametize tests."""
    global usemockserver, useliveserver

    connections = []

    if usemockserver:
        connections.append(ConnectionContainer(MockedConnection, "mockserverlocal", Credentials("admin", "password", "mock"), True))

    if useliveserver and 'ui' in metafunc.fixturenames:
        if live_server and socket.gethostbyname(live_server.hostname):
            live_server_session = requests.Session()

            warnings.warn("Using live server {0}".format(live_server))
            connections.append(live_server)
        else:
            warnings.warn("Live server {0} unreachable".format(live_server))
            useliveserver = False

    credentialled_connections = {"good": [], "fake": [], "none": []}
    for c in connections:
        good_session = requests.Session()
        credentialled_connections['good'].append(c.clazz(c.hostname, auth=c.goodcredentials, verify=c.verify, existing_session=good_session))
        credentialled_connections['none'].append(c.clazz(c.hostname, auth=None, verify=c.verify))
        credentialled_connections['fake'].append(c.clazz(c.hostname, auth=Credentials("fake", "fake", "fake"), verify=c.verify))

    if 'ui' in metafunc.fixturenames:
        metafunc.parametrize(
            'ui',
            credentialled_connections['good'],
            ids=identifiers_for_test_parameters)

    if 'uimock' in metafunc.fixturenames:
        metafunc.parametrize(
            'uimock',
            credentialled_connections['good'],
            ids=identifiers_for_test_parameters)


def identifiers_for_test_parameters(val):
    return str(val).replace(".", "_")
