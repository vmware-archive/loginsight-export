import pytest

from loginsightexport.shorturl import MalformedShortUrlSlug, UnknownShortUrlSlug, unfurl_short_url


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


def test_parse_failure(ui):
    with pytest.raises(MalformedShortUrlSlug):
        unfurl_short_url(None, "junk")


# TODO: This test currently fails against a live server, since that server almost certainly doesn't know about /s/known. Skip it?
def test_unfurl_success(uimock):
    assert "/expanded/url" == unfurl_short_url(uimock, "/s/known")


def test_unfurl_failure(ui):
    with pytest.raises(UnknownShortUrlSlug):
        unfurl_short_url(ui, "/s/junk")
