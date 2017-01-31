#!/usr/bin/env python

import logging
from .compat import parse_qs, urlunparse, urlparse
from . import USERAGENT
import requests
import warnings
from requests.compat import cookielib


# Copyright © 2017 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the “License”); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an “AS IS” BASIS, without warranties or
# conditions of any kind, EITHER EXPRESS OR IMPLIED. See the License for the
# specific language governing permissions and limitations under the License.


logger = logging.getLogger(__name__)
CSRFHEADER = 'X-CSRF-Token'
CSRFCOOKIE = 'cs'


class ServerError(RuntimeError):
    pass


class Unauthorized(ServerError):
    pass


class TechPreviewWarning(UserWarning):
    def __init__(self, url, msg):
        self.url = url
        self.msg = msg

    def __repr__(self):
        return '{cls}(url={x.url!r}, msg={x.msg!r})'.format(cls=self.__class__.__name__, x=self)


def default_user_agent():
    return "loginsightexporter"


def csrf(session, url, **kwargs):
    """Populate the CSRF header for an upcoming POST/DELETE HTTP request to an Action Bean."""
    logger.debug("Retrieving CSRF token for {0}".format(url))
    session.headers.update({CSRFHEADER: "Fetch", 'Referer': url, 'X-Requested-With': 'XMLHttpRequest'})
    p = urlparse(url)
    csrf_url = urlunparse((p.scheme, p.netloc, "/csrf", None, None, None))
    r = session.get(csrf_url, **kwargs)
    session.headers.update({CSRFHEADER: r.headers[CSRFHEADER]})
    logger.debug("Got CSRF token for {0}: {1}".format(url, r.headers[CSRFHEADER]))
    return r.headers[CSRFHEADER]


class Credentials(requests.auth.AuthBase):
    """A JSESSIONID cookie is included in each HTTP request.
    Based on http://docs.python-requests.org/en/master/_modules/requests/auth/"""

    def __init__(self, username, password, provider, reuse_session=None):
        self.username = username
        self.password = password
        self.provider = provider
        self._requests_session = reuse_session or requests.Session()
        self.sessionId = None

    def get_session(self, previousresponse, **kwargs):
        """Perform a session login and return a new cookiejar containing a JSESSIONID."""
        if self.username is None or self.password is None:
            raise Unauthorized("Cannot authenticate without username/password")
        logger.info("Attempting to authenticate as {0}".format(self.username))

        authdict = {"username": self.username, "password": self.password, "authMethod": self.provider, '_eventName': 'loginAjax'}
        if authdict['authMethod'] == "Local":
            authdict['authMethod'] = "DEFAULT"  # UI refers to "Local" accounts as from the "DEFAULT" provider.

        prep = previousresponse.request.copy()

        # Generate /login url from previously-requested resource url
        prep.prepare_method("post")
        p = urlparse(previousresponse.request.url)
        prep.prepare_url(urlunparse([p.scheme, p.netloc, "/login", None, None, None]), params=None)
        prep.prepare_headers({
            CSRFHEADER: csrf(self._requests_session, prep.url, **kwargs),  # kwargs contains ssl _verify
            "X-Requested-With": "XMLHttpRequest",
            'User-Agent': default_user_agent(),
            "Referer": prep.url
        })
        prep.prepare_cookies(self._requests_session.cookies)
        prep.prepare_body(data=authdict, files=None, json=None)

        # logger.debug("Authentication request: {prep.url}\n  cookies: {session.cookies}\n  headers: {prep.headers}\n  body: {prep.body}".format(session=self._requests_session, prep=prep))
        authresponse = previousresponse.connection.send(prep, **kwargs)  # kwargs contains ssl _verify
        # logger.debug("Got authresponse:\n  cookies: {a.cookies}\n  headers: {a.headers}\n  body: {a.text}".format(a=authresponse))

        try:
            if authresponse.json()['succ']:
                self._requests_session.cookies.update(authresponse.cookies)
                return authresponse.cookies
        except Exception as e:
            logger.exception("Can't parse authresponse JSON: {0}".format(authresponse.text))

        if authresponse.headers.get("pi_requires_login", 'false') == 'true':
            raise Unauthorized("Authentication failed, got header pi_requires_login:true")
        raise Unauthorized("Authentication failed")

    def handle_401(self, r, **kwargs):
        # method signature matches requests.Request.register_hook
        internal_status = r.status_code

        if r.headers.get("pi_requires_login", 'false') == 'true':
            logger.debug("Not authenticated (got header pi_requires_login: {0})".format(r.headers.get("pi_requires_login")))
            internal_status = 401  # If we got back a pi_requires_login=true header, pretend that it was an HTTP/401

        if internal_status not in [401, 440, 404]:
            return r

        logger.debug("Not authenticated (got status {r.status_code} @ {r.request.url})".format(r=r))
        r.content  # Drain previous response body, if any
        # r.close()
        r.raw.release_conn()

        self.sessionId = self.get_session(r, **kwargs)
        self._requests_session.cookies.update(self.sessionId)

        logger.debug("Got new sessionId, replaying request with it: {0}".format(self.sessionId))

        # Now that we have a good session, copy and retry the original request. If it fails again, raise Unauthorized.
        prep = r.request.copy()

        prep.headers.update({
            "X-Requested-With": "XMLHttpRequest",
            'User-Agent': default_user_agent(),
            "Referer": prep.url
        })

        # Add CSRF header to methods with side-effects
        if prep.method not in ["GET", "HEAD", "OPTIONS"]:
            prep.headers[CSRFHEADER] = csrf(self._requests_session, prep.url)  # kwargs contains ssl _verify

        try:
            del prep.headers['Cookie']
        except KeyError:
            pass
        prep.prepare_cookies(self._requests_session.cookies)

        logger.debug("Replay request: {prep.url}".format(prep=prep))
        # logger.debug("  cookies: {prep._cookies}\n  headers: {prep.headers}\n  body: {prep.body}".format(prep=prep))
        replay_response = r.connection.send(prep, **kwargs)
        replay_response.history.append(r)
        replay_response.request = prep
        # logger.debug("Replay response:\n  cookies: {a.cookies}\n  headers: {a.headers}\n  body: {a.text}".format(a=replay_response))

        if replay_response.status_code in [401, 440]:
            raise Unauthorized("Authentication failed", replay_response)
        if replay_response.headers.get("pi_requires_login", 'false') == 'true':
            raise Unauthorized("Authentication failed, got header pi_requires_login:true", replay_response)
        logger.debug("Authenticated successfully.")
        return replay_response

    def __call__(self, r):
        # TODO: If the TTL has expired, or we have no Bearer token at all, we can reasonably expect this
        # TODO.cont: request to fail with 401. In both cases, we could avoid a round-trip to the server.
        # TODO.cont: This is an optimization and does not materially affect success.
        if hasattr(self, 'sessionId') and self.sessionId:
            # If we already have a Session ID cookie, try to use it.
            # If the cookie isn't valid, it'll force a re-login just like a missing one would.
            logger.debug("Reusing existing session cookie")
            self._requests_session.cookies.update(self.sessionId)

        # Add CSRF header to methods with side-effects
        if r.method not in ["GET", "HEAD", "OPTIONS"]:
            r.headers[CSRFHEADER] = csrf(self._requests_session, r.url)  # kwargs contains ssl _verify

        # The two above processes have updated the session's cookies. Recreate the Cookie header from them.
        try:
            del r.headers['Cookie']
        except KeyError:
            pass
        r.prepare_cookies(self._requests_session.cookies)

        # Attempt the request. If it fails, generate a new sessionId
        r.register_hook('response', self.handle_401)
        return r

    def __repr__(self):
        return '{cls}(username={x.username!r}, password=..., provider={x.provider!r})'.format(cls=self.__class__.__name__, x=self)


class BlockPIDLTokenCookies(cookielib.DefaultCookiePolicy):
    """Ignore cookies which look like 4bb1453e-8aed-49eb-827e-928e1b56c3a0_pi_dl_token1483338115000=true;"""
    def set_ok(self, cookie, request):
        if '_pi_dl_token' in cookie.name:
            logger.debug("Ignoring {0}".format(cookie))
            return False
        return cookielib.DefaultCookiePolicy.set_ok(self, cookie, request)  # Use instead of super() for py27 compatability


class Connection(object):
    """Low-level HTTP transport connecting to a remote Log Insight server's API.
    Attempts requests to the server which require authentication. If requests fail with HTTP 401 Unauthorized,
    obtains a session bearer token and retries the request.
    You should probably use the :py:class:: Server class instead"""

    def __init__(self, hostname, port=443, ssl=True, verify=True, auth=None, existing_session=None):
        self._requestsession = existing_session or requests.Session()
        self._requestsession.cookies.set_policy(BlockPIDLTokenCookies())
        self._hostname = hostname
        self._port = port
        self._ssl = ssl

        self._requestsession.verify = verify
        self._verify = verify
        self._authprovider = auth

        self._apiroot = '{method}://{hostname}:{port}'.format(method='https' if ssl else 'http',
                                                                     hostname=hostname, port=port)

        self._requestsession.headers.update({'User-Agent': default_user_agent()})

        if auth:
            auth._requests_session = self._requestsession

        logger.debug("Created {0}".format(self))

    @classmethod
    def copy_connection(cls, connection):
        return cls(hostname=connection._hostname,
                   port=connection._port,
                   ssl=connection._ssl,
                   verify=connection._verify,
                   auth=connection._authprovider,
                   existing_session=connection._requestsession)

    def _call(self, method, url, data=None, json=None, params=None, sendauthorization=True, stream=False):
        r = self._requestsession.request(
            method=method,
            url=self._apiroot + url,
            data=data,
            json=json,
            verify=self._verify,
            auth=self._authprovider if sendauthorization else None,
            params=params,
            stream=stream,
            allow_redirects=False,
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'User-Agent': default_user_agent()
            }
        )
        try:
            payload = r.json()
        except:
            payload = r.text
        if 'Warning' in r.headers:
            warnings.warn(TechPreviewWarning(url, r.headers.get('Warning')), stacklevel=3)
        if r.status_code in [401, 440]:
            raise Unauthorized(r.status_code, payload)
        return r

    def post(self, url, data=None, json=None, params=None, sendauthorization=True):
        """
        Attempt to post to server with current authorization credentials.
        If post fails with HTTP 401 Unauthorized, authenticate and retry.
        """
        return self._call(method="POST",
                          url=url,
                          data=data,
                          json=json,
                          sendauthorization=sendauthorization,
                          params=params)

    def get(self, url, params=None, sendauthorization=True, stream=False):
        return self._call(method="GET",
                          url=url,
                          sendauthorization=sendauthorization,
                          params=params,
                          stream=stream)

    def delete(self, url, params=None, sendauthorization=True):
        return self._call(method="DELETE",
                          url=url,
                          sendauthorization=sendauthorization,
                          params=params)

    def put(self, url, data=None, json=None, params=None, sendauthorization=True):
        """Attempt to post to server with current authorization credentials. If post fails with HTTP 401 Unauthorized, retry."""
        return self._call(method="PUT",
                          url=url,
                          data=data,
                          json=json,
                          sendauthorization=sendauthorization,
                          params=params)

    def patch(self, url, data=None, json=None, params=None, sendauthorization=True):
        """Attempt to post to server with current authorization credentials. If post fails with HTTP 401 Unauthorized, retry."""
        return self._call(method="PATCH",
                          url=url,
                          data=data,
                          json=json,
                          sendauthorization=sendauthorization,
                          params=params)

    def log(self, message, includeuseragent=True):
        """Emit a log message into ui_runtime.log on the remote server."""
        srvmessage = message if not includeuseragent else "%s %s" % (USERAGENT, message)
        response = self.post("/internal/logger", data={
            b"logMessage": srvmessage,
            b"logLevel": b"info",
            b"_eventName": b"log"
        })
        serverlogger = logger.getChild("ServerLogger").getChild("ui_runtime.log")
        if response.status_code != 200:
            serverlogger.warning("Attempt to log to server failed with HTTP status %d" % response.status_code)
        serverlogger.info(msg=message)
        return response.status_code == 200

    def ping(self):
        self.get("/")

    def __repr__(self):
        """Human-readable and machine-executable description of the current connection."""
        return '{cls}(hostname={x._hostname!r}, port={x._port!r}, ssl={x._ssl!r}, verify={x._verify!r}, auth={x._authprovider!r})'.format(cls=self.__class__.__name__, x=self)


class query(object):
    """Create a query via helper bean. Save the reflected PIQL. Cancel the query."""

    def __init__(self, uidriver, url):
        self.uidriver = uidriver
        self.url = url

        if self.url[0] != '/':
            raise ValueError("Invalid url, doesn't start with '/': {0}".format(self.url))

    def generateToken(self):
        r = self.uidriver.get('/logcancel', params={"_eventName": "generateSearchCancelToken"})
        cancelToken = r.json()['cancelToken']
        logger.info("Retrieved new cancelToken %s" % cancelToken)
        return cancelToken

    def cancel(self, cancelToken):
        """Attempt to cancel an outstanding query. Query may have already been cancelled, so log but ignore failure."""
        r = self.uidriver.post("/logcancel", data={"cancelToken": cancelToken, "_eventName": "cancelSearch"})

        if r.status_code != 200 or not r.json()['succ']:
            # Cancellation requested. Note that query cancellation is best effort and may not always succeed.
            logger.warning("Cancellation failed with HTTP status %d: %s" % (r.status_code, r.json()))
            return False
        return True

    @property
    def piql(self):
        """Create a connection to the remote system, execute the query, retrieve PIQL from server, cancel the query."""

        cancelToken = self.generateToken()

        self.uidriver.log("Exporter starting PIQL discover.")
        logger.warning("Starting query with cancelToken %s" % cancelToken)

        r = self.uidriver.get(self.url, params={"paramsHelper.cancelToken": cancelToken})
        response = r.json()

        logger.warning("Got response to query %s" % response['cancelToken'])
        if response['cancelToken'] != cancelToken:  # Returned cancelToken should match the requested one.
            logger.warning("Request cancelToken {0} does not match returned cancelToken {1}".format(cancelToken, response['cancelToken']))

        if 'cancelled' not in response or not response['cancelled']:
            logger.debug("Query did not auto-cancel, canceling...")
            self.cancel(response['cancelToken'])
        else:
            logger.debug(response)
            logger.debug("Query auto-cancelled, no cancellation required.")
        if 'chartPiqlQuery' in response:
            logger.debug("Retrieved chart piql %s" % response['chartPiqlQuery'])
            return response['chartPiqlQuery']
        if 'messagePiqlQuery' in response:
            logger.debug("Retrieved message piql %s" % response['messagePiqlQuery'])
            return response['messagePiqlQuery']
        raise RuntimeError(response)


class AggregateQuery(object):
    def __init__(self, connection, url):
        """Given a url like /logcharting?paramsHelper..., retrieve response and produce useful dictionaries"""
        r = connection.get(url)
        body = r.json()
        logger = logging.getLogger(__name__)

        self.elapsed = r.elapsed

        if len(body['groupByHeaders']) != 1:
            raise RuntimeError("This query produced multiple groupings. Set the query to group by time only.")
        if not body['groupByHeaders'][0]['isTime']:
            raise RuntimeError("This query is grouped by something other than time. Set the query to group by time only.")

        for k, v in body.items():
            setattr(self, k, v)

        self.bins = [(x['groupByValues'][0]['val'], x['groupByValues'][0]['endVal'], x['aggregationValues'][0]) for x in body['rows']]

        logger.debug("Retrieved results: {0}".format(self))

    def __repr__(self):
        """Human-readable representation of query result summary."""
        return '<{cls}: elapsed={x.elapsed}, {lenbins} bins containing {n} events>'.format(
            cls=self.__class__.__name__,
            x=self,
            lenbins=len(self.bins),
            n=sum([b[2] for b in self.bins])
        )
