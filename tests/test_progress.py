from loginsightexport.progress import ProgressBar
import time
from datetime import timedelta
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


def test_progressbar_iterator(capsys):
    alist = [1, 2, 3]

    def fn():
        with ProgressBar(alist) as p:
            for i in p:
                yield i

        out, err = capsys.readouterr()
        assert "33" in out
        assert "100" in out
    assert list(fn()) == alist


def test_progressbar_output(capsys):
    alist = [1, 2, 3]
    with ProgressBar(alist, columns=5, suffix="suffix") as p:
        list(p)

    out, err = capsys.readouterr()

    assert len(alist) + 1 == out.count("\r")
    assert 1 == out.count("\n")
    assert "100.0% {n}/{n} suffix".format(n=len(alist)) in out


def test_silent_progress_context(capsys):
    with ProgressBar([1], columns=5, suffix="suffix", quiet=True) as p:
        print("a")
        time.sleep(0.1)
        print("b")
    out, err = capsys.readouterr()
    assert out == "a\nb\n"
    assert p.longest_line == 0
    assert p.duration > timedelta(0)


def test_exceptions(capsys):
    ordering = []

    with pytest.raises(ZeroDivisionError) as e:
        with ProgressBar([1, 2, 3], columns=5, suffix="suffix") as c:
            ordering.append("top")
            for num in c:
                ordering.append("loop%d" % num)
                if num == 2:
                    ordering.append('Exception')
                    raise ZeroDivisionError()
            ordering.append("endwith")
        ordering.append("outsidewith")

    out, err = capsys.readouterr()

    assert 'Aborted' in out
    assert ordering == ['top', 'loop1', 'loop2', 'Exception']
