import json
import logging
import time

from loginsightexport.compat import parse_qsl
from .utils import RandomDict, requiresauthentication, User, Session


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


class MockedSessionsMixin(object):
    def __init__(self, **kwargs):
        super(MockedSessionsMixin, self).__init__(**kwargs)

        self.sessions_known = RandomDict()
        self.users_known = [User('admin', 'password', 'mock', "012345678-9ab-cdef-0123-456789abcdef")]

        self.register_uri('POST', '/api/v1/sessions', text=self.session_new, status_code=200)
        self.register_uri('GET', '/api/v1/sessions/current', text=self.session_current, status_code=200)

        self.register_uri('POST', '/login', text=self.login, status_code=200)

    @requiresauthentication
    def session_current(self, request, context, session_id, user_id):
        """Attempt to create a new session with provided credentials."""
        return json.dumps(self.sessions_known[session_id]._asdict())

    def session_new(self, request, context):
        """Attempt to create a new session with provided credentials."""
        self.session_timeout()
        attempted_credentials = request.json()
        for u in self.users_known:
            if u.username == attempted_credentials['username'] and u.provider == attempted_credentials['provider']:
                if u.password == attempted_credentials['password']:
                    mockserverlogger.info("Successful authentication as {u.username} = {u.userId}".format(u=u))
                    context.status_code = 200
                    sessionId = self.sessions_known.append(Session(u.userId, 1800, time.time()))
                    return json.dumps({"userId": u.userId, "sessionId": sessionId, "ttl": 1800})
                else:  # wrong password, bail out
                    mockserverlogger.warning("Correct username but invalid password (which is OK to say, because this is a mock)")
                    break
        context.status_code = 401
        return json.dumps({"errorMessage": "Invalid username or password.", "errorCode": "FIELD_ERROR"})

    def session_timeout(self):
        """Reap any expired (TTL) sessions"""
        for sessionId in self.sessions_known:
            if (time.time() - self.sessions_known[sessionId].created) > self.sessions_known[sessionId].ttl:
                mockserverlogger.warning("Session {0} expired".format(sessionId))
                del self.sessions_known[sessionId]

    def session_inspection_user_list(self):
        return set([usersession.userId for usersession in self.sessions_known.values()])

    def login(self, request, context):
        """Attempt to create a new session with provided credentials."""
        self.session_timeout()
        attempted_credentials = dict(parse_qsl(request.text))

        assert attempted_credentials['_eventName'] == 'loginAjax'

        for u in self.users_known:
            if u.username == attempted_credentials['username'] and u.provider == attempted_credentials['authMethod']:
                if u.password == attempted_credentials['password']:
                    mockserverlogger.info("Successful authentication as {u.username} = {u.userId}".format(u=u))
                    context.status_code = 200
                    sessionId = self.sessions_known.append(Session(u.userId, 1800, time.time()))
                    context.cookies.set('JSESSIONID', sessionId)
                    return json.dumps({"succ": True})
                else:  # wrong password, bail out
                    mockserverlogger.warning("Correct username but invalid password (which is OK to say, because this is a mock)")
                    break
        context.status_code = 401
        return json.dumps({"errorMessage": "Invalid username or password.", "errorCode": "FIELD_ERROR"})
