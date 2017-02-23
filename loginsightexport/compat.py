# -*- coding: utf-8 -*-

# Compatibility imports for different python versions

import time
import warnings


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

# TODO: This could be replaced by https://pythonhosted.org/six/#module-six.moves.urllib.parse

try:
    # Python 3
    # noinspection PyCompatibility
    from urllib.parse import parse_qs, urlunparse, urlparse, parse_qsl, urlencode  # noqa
except ImportError:
    # Python 2
    # noinspection PyCompatibility,PyUnresolvedReferences
    from urlparse import parse_qs, urlunparse, urlparse, parse_qsl  # noqa
    from urllib import urlencode  # noqa

try:
    current_time = time.monotonic
except AttributeError:
    current_time = time.time  # Reasonable fallback
    warnings.warn("Using non-monotonic timesource, durations should be taken with a grain of salt")

if not hasattr(__builtins__, 'FileNotFoundError'):
    FileNotFoundError = IOError

if not hasattr(__builtins__, 'RecursionError'):
    class RecursionError(RuntimeError):
        """RecursionError exception compatible with py27"""


raise ImportError("Reasons")
