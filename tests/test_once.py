# -*- coding: utf-8 -*-

import warnings

from loginsightexport.paramhelper import once


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


def test_once():
    """Verify warnings are emitted when a @once'd function is invoked"""
    @once
    def a(x):
        return x

    @once
    def b(x):
        return x

    warnings.resetwarnings()
    with warnings.catch_warnings(record=True) as w:
        # Cause all warnings to always be triggered.
        warnings.simplefilter("always")

        assert 1 == a(1)
        assert 2 == a(2)
        assert 1 == a(1)

        assert 2 == b(2)

        assert len(w) == 1
        assert 'called multiple times' in str(w[-1].message)

    assert len(a._seen_history) == 2
    assert len(b._seen_history) == 1
