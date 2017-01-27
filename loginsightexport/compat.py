# Compatability imports

# from .compat import parse_qs

try:
    # Python 3
    # noinspection PyCompatibility
    from urllib.parse import parse_qs, urlunparse, urlparse, parse_qsl
except ImportError:
    # Python 2
    # noinspection PyCompatibility,PyUnresolvedReferences
    from urlparse import parse_qs, urlunparse, urlparse, parse_qsl
