# -*- coding: utf-8 -*-

import json
import logging
import re

from .utils import requiresauthentication


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


mockserverlogger = logging.getLogger("LogInsightMockAdapter")

short_url_matcher = re.compile('/api/v1/short/(.*)$')


class MockedShortUrlMixin(object):
    def __init__(self, **kwargs):
        super(MockedShortUrlMixin, self).__init__(**kwargs)
        self.slugs_known = {'known': '/expanded/url'}
        self.register_uri('GET', short_url_matcher, text=self.shorturl_callback, status_code=200)

    @requiresauthentication
    def shorturl_callback(self, request, context, session_id, user_id):
        short_slug = short_url_matcher.match(request._url_parts.path).group(1)

        try:
            return json.dumps({'longUrl': self.slugs_known[short_slug]})
        except KeyError:
            context.status_code = 404
            return json.dumps({})
