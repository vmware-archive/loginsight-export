# -*- coding: utf-8 -*-

import logging
import requests
import pytest
import warnings
import socket
from collections import namedtuple

from mock_loginsight_server import MockedConnection
from loginsightexport.uidriver import Connection, Credentials, TechPreviewWarning


# VMware vRealize Log Insight Exporter
# Copyright © 2017 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an “AS IS” BASIS, without warranties or
# conditions of any kind, EITHER EXPRESS OR IMPLIED. See the License for the
# specific language governing permissions and limitations under the License.


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


def checkfile(fspath):
    errors = []
    body = fspath.read()

    if 'Copyright © 2017 VMware, Inc' not in body:
        errors.append("Missing Copyright")
    if 'http://www.apache.org/licenses/LICENSE-2.0' not in body:
        errors.append("Missing License")
    if '# -*- coding: utf-8 -*-' not in body:
        errors.append("Missing utf-8 format")
    return errors


# ad-hoc pytest plugin based on http://doc.pytest.org/en/latest/example/nonpython.html
class BoilerplateVerifyPlugin(object):
    def pytest_collect_file(self, path, parent):
        if path.ext == '.py':  # do not constrain path, all python source files should be marked
            return BoilerplateVerifyItem(path, parent, None)


class BoilerplateVerifyItem(pytest.Item, pytest.File):
    def runtest(self):
        errors = checkfile(self.fspath)
        if errors:
            raise BoilerplateVerifyError("\n".join(errors))

    def repr_failure(self, excinfo):
        if excinfo.errisinstance(BoilerplateVerifyError):
            return excinfo.value.args[0]
        return super(BoilerplateVerifyItem, self).repr_failure(excinfo)

    def reportinfo(self):
        return (self.fspath, -1, "Required declaration: %s" % self.fspath)


class BoilerplateVerifyError(Exception):
    """indicates an error during copyright/license checks. """


def pytest_configure(config):
    config.pluginmanager.register(BoilerplateVerifyPlugin())
