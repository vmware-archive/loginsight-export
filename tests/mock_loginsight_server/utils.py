# -*- coding: utf-8 -*-

from functools import wraps
import logging
import uuid
import re
from collections import namedtuple


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


mockserverlogger = logging.getLogger(__name__)

trailing_anything_pattern = re.compile('.*/(.*)$')
trailing_guid_pattern = re.compile('.*/([a-f0-9-]+)$')
license_url_matcher = re.compile('/api/v1/licenses/([a-f0-9-]+)$')


User = namedtuple("User", field_names=["username", "password", "provider", "userId"])
Session = namedtuple("Session", field_names=["userId", "ttl", "created"])


class RandomDict(dict):
    """Subclass of `dict` that adds a list-like `append` method that generates a unique UUID key"""
    def append(self, value):
        key = str(uuid.uuid4())
        while key in self:
            key = str(uuid.uuid4())
        self[key] = value
        return key


def requiresauthentication(fn):
    """Server mock; fail any request which does not contain the expected Authorization header with HTTP/401"""
    @wraps(fn)
    def wrapper(self, request, context):
        cookie_id = request._request._cookies.get('JSESSIONID')
        if cookie_id is not None and cookie_id in self.sessions_known:
            mockserverlogger.info("Verified bearer has a valid JSESSIONID")
            return fn(self, request, context, cookie_id, self.sessions_known[cookie_id].userId)

        session_id = request.headers.get('Authorization', "")[7:]
        if session_id is not None and session_id in self.sessions_known:  # TODO: Don't ignore TTL
            mockserverlogger.info("Verified bearer has a valid sessionId")
            return fn(self, request, context, session_id, self.sessions_known[session_id].userId)
        context.status_code = 401
        return ""
    return wrapper
