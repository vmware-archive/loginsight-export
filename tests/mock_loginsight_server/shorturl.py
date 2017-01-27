import json
import logging
import time
import re

from .utils import RandomDict, requiresauthentication, User, Session, trailing_anything_pattern


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
