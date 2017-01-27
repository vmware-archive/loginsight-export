import re


class MalformedShortUrlSlug(RuntimeError):
    pass


class UnknownShortUrlSlug(RuntimeError):
    pass


def unfurl_short_url(connection, slug):
    pattern = re.compile('^/s/(.+)')
    m = pattern.match(slug)
    if m is None:
        raise MalformedShortUrlSlug(slug)
    r = connection.get("/api/v1/short/%s" % m.group(1))
    try:
        return r.json()['longUrl']
    except KeyError:
        raise UnknownShortUrlSlug(slug)
