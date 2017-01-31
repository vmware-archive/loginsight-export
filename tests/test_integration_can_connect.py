# -*- coding: utf-8 -*-

import warnings


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


def test_get_version(ui):
    with warnings.catch_warnings(record=True) as w:
        assert 'version' in ui.get("/api/v1/version").json()
    ui._requestsession.close()


def test_get_version_without_credentials(ui):
    assert 'Credentials' in str(ui)
    ui._authprovider = None
    assert 'Credentials' not in str(ui)

    with warnings.catch_warnings(record=True) as w:
        assert 'version' in ui.get("/api/v1/version").json()
    ui._requestsession.close()
