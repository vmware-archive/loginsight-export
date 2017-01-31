# -*- coding: utf-8 -*-

import collections
import pytest


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


def test_exception_in_context_manager_plain():
    ordering = []

    class Ctx(collections.Iterator):
        def __init__(self, iterable):
            ordering.append("init")
            self._iterator = iter(iterable)

        def __enter__(self):
            ordering.append("enter")
            return self

        def __iter__(self):
            ordering.append("iter")
            return self

        def __next__(self):
            ordering.append("next")
            return next(self._iterator)

        next = __next__

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                ordering.append("Exception")
            ordering.append("exit")
            return

    with pytest.raises(Exception):
        with Ctx([1, 2, 3]) as c:
            for num in c:
                ordering.append("loop%d" % num)
                if num == 2:
                    ordering.append('Exception')
                    raise Exception

    assert 'Exception' in ordering
