# -*- coding: utf-8 -*-

"""
Given a set of time ranges as aggregate counts, produce a best-fit set of windows.
"""

import logging
from itertools import tee

from .compat import RecursionError

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


logger = logging.getLogger(__name__)


def map_dict_to_list(d, width):
    """
    Given a dictionary -> {start: quantity, start: quantity, ...}
    Return a list of tuples [(start, end, quantity), (start, end, quantity), ...]
    """
    assert(width >= 0)
    for startTimeMillis in d:
        yield((int(startTimeMillis), int(startTimeMillis) + width, d[startTimeMillis]))


def sorted_by_startTimeMillis(bins):
    return sorted(bins, key=lambda b: b[0])


def overlapping(bins):
    """
    Given a sorted list bins, check whether any are overlapping [....{;;;]----}.
    Touching is OK: [....]{----}"""
    s, e = 0, 0
    for b in bins:
        if s < b[1] and b[0] < e:
            return True
        s, e = b[0], b[1]
    return False


def contiguous(bins):
    a, b = tee(bins)
    next(b, None)
    for ia, ib in zip(a, b):  # for each pair of consecutive items [(1,2), (2,3), (3,4), ... (ia,ib)]
        if ia[1] + 1 != ib[0]:  # start of item b matches end of item a, these are contiguous pairs
            logger.debug("In the comparison of ia={ia!r} with ib={ib!r}, observe that {ia[1]} != {ib[0]}".format(ia=ia, ib=ib))
            return False
    return True


def merge(bins, maximum=20000):
    """Merge two adjacent bins, such that the total coverage is the same before and after."""
    # This is an optional optimization. It would be premature to implement this early.
    i = iter(bins)
    prev = next(i)
    for nb in i:
        if contiguous([prev, nb]) and nb[2] + prev[2] <= maximum:
            # Combine adjacent items
            combined = (prev[0], nb[1], prev[2] + nb[2])
            logger.debug("Combined {0} + {1} to new bin {2}".format(prev, nb, combined))
            prev = combined
            continue
        logger.debug("-------- {0}".format(prev))
        yield prev
        prev = nb
    if prev is not None:
        logger.debug("-------- {0}".format(prev))
        yield prev


def patch_bins_at_boundaries(boundary_bin, bins):
    """
    A query response produces a list of bins.
    The returned first and last bins might not align with the requested range. Instead they are a superset.
    However, the quantity of results XXXXX within that bin is still correctly represented.

    [binstart.........|requestedstart-XXXXXXXXXXXXXXXX-binend]

    This is akin to asking "How many hours were there after noon yesterday?" and getting a response "There were 12 hours yesterday."

    The query's boundary_bin's start or end might reside within a returned bin. If so, modify the returned bin to the correct start/end.
    """
    start = boundary_bin[0]
    end = boundary_bin[1]
    for b in bins:
        logger.debug("Considering boundary {boundary_bin} vs bin {b}".format(boundary_bin=boundary_bin, b=b))
        if b[0] < start < b[1] and b[0] < end < b[1]:  # There's only one bin, and it's bigger than the whole desired start-end range. Replace it.
            logger.debug("patched full {0} -> {1}".format(b, (start, end, b[2])))
            yield (start, end, b[2])
        elif b[0] < start < b[1]:  # if the desired start sits inside this bin, modify the bin with a new start
            logger.debug("patched start {0} -> {1}".format(b, (start, b[1], b[2])))
            yield (start, b[1], b[2])
        elif b[0] < end and end < b[1]:  # if the desired end sits inside this bin, modify the bin with a new end
            logger.debug("patched end {0} -> {1}".format(b, (b[0], end, b[2])))
            yield (b[0], end, b[2])
        else:  # A normal bin in the middle
            yield b


def split(bins, fetch_subset_fn, maximum=20000):
    for b in bins:
        if b[2] > maximum:
            logger.debug("This bin %s is larger than the maximum, split it apart" % str(b))
            newbins = fetch_subset_fn(b)
            if [b] == newbins:
                if b[0] == b[1]:
                    raise RecursionError("This bin {b} is 0ms long, so the server won't subdivide it any further, but there's more than {max} items in it. Use a larger --max".format(b=b, max=maximum))
                raise RecursionError("The server won't subdivide the bin {b} any further, but there's more than {max} items in it. Please report this as a bug.".format(b=b, max=maximum))
            count_in_new_bins = 0
            for newbin in split(newbins, fetch_subset_fn, maximum):
                yield newbin
                count_in_new_bins += newbin[2]
            if count_in_new_bins != b[2]:
                raise RecursionError("The server expanded bin {b} to contain {i} items".format(b=b, i=count_in_new_bins))
        else:
            yield b


def asplit(bins, splitfn, maximum=20000):
    r = []
    for b in bins:
        if b[2] > maximum:
            logger.debug("This bin %s is larger than the maximum, split it apart" % str(b))
            newbins = splitfn(b, splitfn, maximum=maximum)
            if bins == newbins:
                raise RecursionError("{0} -> {1} is not splitting bins: {2}".format(__name__, splitfn, bins))
            for newbin in split(newbins, splitfn, maximum):
                r.append(newbin)
        else:
            r.append(b)
    return r
