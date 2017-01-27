import pytest

from loginsightexport.shorturl import MalformedShortUrlSlug, UnknownShortUrlSlug, unfurl_short_url


def test_parse_failure(ui):
    with pytest.raises(MalformedShortUrlSlug):
        unfurl_short_url(None, "junk")


# TODO: This test currently fails against a live server, since that server almost certainly doesn't know about /s/known. Skip it?
def test_unfurl_success(uimock):
    assert "/expanded/url" == unfurl_short_url(uimock, "/s/known")


def test_unfurl_failure(ui):
    with pytest.raises(UnknownShortUrlSlug):
        unfurl_short_url(ui, "/s/junk")
