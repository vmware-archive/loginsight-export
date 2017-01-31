# -*- coding: utf-8 -*-

from __future__ import division

import pytest
import logging

from loginsightexport.binfit import map_dict_to_list, sorted_by_startTimeMillis, overlapping, split, merge, patch_bins_at_boundaries
from itertools import tee


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
logger.setLevel(logging.DEBUG)

FIXTURE_BINS = {'1479092400000': 51186836, '1479038400000': 50901245, '1479060000000': 49671085, '1479135600000': 46906946, '1478980800000': 47544747, '1479178800000': 58169193,
                '1478815200000': 47641527, '1478786400000': 60183092, '1479009600000': 49607569, '1479222000000': 46471020, '1478930400000': 48586701, '1479250800000': 53577544,
                '1479103200000': 52977527, '1478793600000': 49829418, '1478826000000': 54362380, '1478858400000': 60403137, '1479078000000': 54261366, '1479182400000': 49462306,
                '1479013200000': 47103500, '1479027600000': 47640868, '1478782800000': 5598455, '1478988000000': 48017284, '1479218400000': 50553889, '1478912400000': 52759360,
                '1478955600000': 46987633, '1479002400000': 51799790, '1478880000000': 50552098, '1479031200000': 47894566, '1478818800000': 52413012, '1478937600000': 48417215,
                '1478934000000': 49010087, '1479272400000': 46846152, '1479121200000': 56335145, '1479096000000': 47141058, '1479200400000': 46995285, '1478851200000': 49610461,
                '1479211200000': 55286154, '1478970000000': 49689840, '1478811600000': 48283656, '1479045600000': 51098189, '1479085200000': 49017383, '1479056400000': 50532680,
                '1478962800000': 47472086, '1478984400000': 48745384, '1479139200000': 51058292, '1478797200000': 48051727, '1479164400000': 48463166, '1478898000000': 51035119,
                '1478908800000': 50449533, '1479006000000': 57977941, '1479229200000': 47129794, '1479114000000': 51760091, '1479049200000': 47387907, '1479124800000': 49536541,
                '1478865600000': 48731655, '1478977200000': 48243369, '1478944800000': 48421997, '1479240000000': 57009367, '1479171600000': 48727000, '1479175200000': 50919386,
                '1479196800000': 47235088, '1479225600000': 48485618, '1479146400000': 47523831, '1478833200000': 47478339, '1478919600000': 52168625, '1479254400000': 50863209,
                '1479074400000': 50592077, '1479099600000': 47266704, '1478844000000': 45905393, '1478829600000': 57973084, '1478840400000': 46248364, '1478872800000': 53224550,
                '1478998800000': 53837665, '1478822400000': 53491245, '1478869200000': 48421853, '1479160800000': 47379316, '1478901600000': 49817685, '1478800800000': 46683129,
                '1478991600000': 49053974, '1478808000000': 50856843, '1479088800000': 51120129, '1479106800000': 51538045, '1479153600000': 45421487, '1478862000000': 61020405,
                '1479024000000': 46951027, '1479232800000': 55243430, '1479236400000': 54538389, '1479063600000': 50287384, '1479268800000': 51151645, '1479150000000': 47938379,
                '1478923200000': 50856036, '1479117600000': 50802422, '1479142800000': 47097414, '1479128400000': 51345233, '1478790000000': 52856426, '1479207600000': 55870395,
                '1478883600000': 56707840, '1478952000000': 49505449, '1478926800000': 51184578, '1479020400000': 47722544, '1479189600000': 50274421, '1479110400000': 49711933,
                '1479016800000': 47079008, '1479067200000': 54786513, '1478890800000': 57212154, '1479186000000': 48669010, '1478959200000': 48329113, '1479204000000': 53425178,
                '1479258000000': 58606045, '1478854800000': 51861659, '1478973600000': 49851481, '1479168000000': 47992310, '1478941200000': 46796686, '1478948400000': 50543490,
                '1479081600000': 50587625, '1478876400000': 51200462, '1478836800000': 46488723, '1479276000000': 21136835, '1479243600000': 53784620, '1479132000000': 46043978,
                '1479265200000': 48964849, '1478905200000': 52513662, '1479157200000': 46408160, '1479261600000': 51067459, '1479193200000': 48446192, '1479042000000': 48366740,
                '1478916000000': 50675084, '1478804400000': 48327089, '1478887200000': 54680435, '1478966400000': 49987243, '1478847600000': 46456133, '1479052800000': 46911863,
                '1479034800000': 49870675, '1479070800000': 54855412, '1479214800000': 52851587, '1478995200000': 57973805, '1478894400000': 54002885, '1479247200000': 51542622}
FIXTURE_WIDTH = 3600000


def test_convert_to_list():
    r = map_dict_to_list(FIXTURE_BINS, FIXTURE_WIDTH)
    for _ in r:
        assert _[0] + FIXTURE_WIDTH == _[1]  # generated end datestamps
        if _[0] == 1479135600000:
            assert _[1] == 1479135600000 + FIXTURE_WIDTH
            assert _[2] == 46906946


def test_fixture_contiguous():
    r = sorted_by_startTimeMillis(map_dict_to_list(FIXTURE_BINS, FIXTURE_WIDTH))
    a, b = tee(r)
    next(b, None)
    for ia, ib in zip(a, b):  # for each pair of consecutive items [(1,2), (2,3), (3,4), ... (ia,ib)]
        assert ia[1] == ib[0]  # start of item b matches end of item a, these are contiguous pairs


def test_ensure_no_overlap():
    assert not overlapping([(1, 2, 0), (2, 3, 0), (3, 4, 0)])  # touching
    assert not overlapping([(1, 2, 0), (2, 2, 0), (2, 3, 0)])  # 0 width touching   [....]()[....]

    assert overlapping([(1, 3, 0), (2, 3, 0)])  # overlapping [....{;;;]----}
    assert overlapping([(1, 3, 0), (1, 3, 0)])  # same size   (;;;)
    assert overlapping([(1, 2, 0), (1, 3, 0)])  # same start  (;;;]---}
    assert overlapping([(1, 3, 0), (2, 3, 0)])  # same end    [...{;;;)
    assert overlapping([(1, 4, 0), (2, 3, 0)])  # b inside a  [....{;;;}....]
    assert overlapping([(1, 4, 0), (2, 2, 0)])  # 0b inside a [....()....]

    bins = sorted_by_startTimeMillis(map_dict_to_list(FIXTURE_BINS, FIXTURE_WIDTH))
    assert not overlapping(bins)


def assert_binsize_remained_the_same(pre, post):
    presplit_count = sum([x[2] for x in pre])
    postsplit_count = sum([x[2] for x in post])
    assert presplit_count == postsplit_count

    presplit_coveredspan = sum([x[1] - x[0] for x in post])
    postsplit_coveredspan = sum([x[1] - x[0] for x in post])
    assert presplit_coveredspan == postsplit_coveredspan


@pytest.mark.parametrize("bins, maximum, targetquantity, name", [
    ([(80, 180, 60), (180, 280, 3), (280, 380, 5)], 20, 6, "split first element twice"),
    ([(0, 1, 16)], 2, 8, "recursive"),
    ([(0, 1, 1000)], 10, int(1000 / 7.8125), "recursive"),
    ([(0, 1, 10), (1, 2, 10), (2, 3, 10)], 20, 3, "untouched"),
    ([(0, 1, 20), (1, 2, 10), (2, 3, 10)], 15, 4, "first exceeds, remaining untouched"),
    ([(0, 1, 10), (1, 2, 10), (2, 3, 20)], 15, 4, "last exceeds, remaining untouched"),
], ids=str)
def test_bin_splitting(bins, maximum, targetquantity, name):
    del name  # unused variable, only for naming the test

    assert not overlapping(bins)

    def fetch_subset_fn(bin, report_callback=False):
        del report_callback  # unused variable, only present for mocking
        halfway_time = (bin[0] + bin[1]) / 2
        halfway_value = bin[2] / 2
        new_bins = [
            (bin[0], halfway_time, halfway_value),
            (halfway_time, bin[1], halfway_value)
        ]
        return sorted_by_startTimeMillis(new_bins)

    new_bins = list(split(bins, fetch_subset_fn, maximum))

    # The sum of range sizes and quantities remain consistent across split/combine operations
    assert_binsize_remained_the_same(bins, new_bins)
    assert len(new_bins) == targetquantity

    def assert_only(*unused):
        del unused  # unused variables in mock
        raise RuntimeError("Unsplit buckets still exceed maximum")
    maybe_stable_bins = list(split(new_bins, assert_only, maximum=maximum))
    assert new_bins == maybe_stable_bins


@pytest.fixture
def touching_bins():
    bins = [(100, 200, 9), (200, 300, 8), (300, 400, 7), (400, 500, 1)]
    assert not overlapping(bins)
    return bins


@pytest.fixture
def sparse_bins():
    bins = [(100, 200, 2), (400, 500, 3)]
    assert not overlapping(bins)
    return bins


@pytest.mark.parametrize("bins, maximum, targetquantity, name", [
    ([(100, 199, 2), (200, 299, 3)], 20, 1, "sparse"),
    ([(100, 199, 9), (200, 299, 8), (300, 399, 7), (400, 499, 1)], 20, 2, "two pairs"),
    ([(100, 199, 10), (200, 299, 10), (300, 399, 10)], 20, 2, "two merged one remains"),
    ([(100, 199, 20), (200, 299, 10), (300, 399, 10)], 20, 2, "first exceeds, remaining merged"),
    ([(100, 199, 10), (200, 299, 10), (300, 399, 20)], 20, 2, "last exceeds, remaining merged"),
], ids=str)
def test_bins_merged(bins, maximum, targetquantity, name):
    del name  # unused variable, only for naming the test

    newbins = list(merge(bins, maximum=maximum))
    assert newbins != bins

    # The sum of range sizes and quantities remain consistent across split/combine operations
    assert_binsize_remained_the_same(bins, newbins)
    assert len(newbins) == targetquantity

    def assert_only(*unused):
        del unused  # unused variables in mock
        raise RuntimeError("Unsplit buckets still exceed maximum")
    stablebins = list(split(newbins, assert_only, maximum=maximum))
    assert newbins == stablebins


@pytest.mark.parametrize("bins, maximum, name", [
    ([(100, 200, 2), (400, 500, 3)], 20, "sparse"),
    ([(100, 200, 2), (200, 300, 99)], 20, "second exceeds"),
    ([(100, 200, 99), (200, 300, 1)], 20, "first exceeds"),
    ([(100, 200, 99), (200, 300, 99)], 20, "all exceeds")
], ids=str)
def test_bins_should_not_merge(bins, maximum, name):
    del name  # unused variable, only for naming the test

    untouched = list(merge(bins, maximum=maximum))
    assert untouched == bins


@pytest.mark.parametrize("bins, overview, expected, name", [
    ([(1, 5, 2), (6, 10, 3)], (-100, 100, None), [(1, 5, 2), (6, 10, 3)], "superset of all bins (sparse response)"),
    ([(1, 5, 2), (6, 10, 3)], (1, 10, None), [(1, 5, 2), (6, 10, 3)], "perfectly aligned already"),
    ([(1, 5, 2), (6, 10, 3)], (3, 10, None), [(3, 5, 2), (6, 10, 3)], "intersection with first bin"),
    ([(1, 5, 2), (6, 10, 3)], (1, 7, None), [(1, 5, 2), (6, 7, 3)], "intersection with last bin"),
    ([(1, 5, 2), (6, 10, 3)], (3, 7, None), [(3, 5, 2), (6, 7, 3)], "intersection with first and last bin"),
    ([(1, 5, 2)], (3, 4, None), [(3, 4, 2)], "intersection with only bin"),
], ids=str)
def test_patch_bins_at_boundaries(bins, overview, expected, name):
    del name  # unused variable, only for naming the test

    r = list(patch_bins_at_boundaries(bins=bins, boundary_bin=overview))
    assert r == expected
