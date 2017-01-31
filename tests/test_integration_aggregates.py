import pytest

from loginsightexport.shorturl import MalformedShortUrlSlug, UnknownShortUrlSlug, unfurl_short_url
from loginsightexport.paramhelper import ExplorerUrlParse
from loginsightexport.uidriver import AggregateQuery

from loginsightexport.compat import parse_qs, urlunparse, urlparse, parse_qsl


EXAMPLE_EXPLORER_URL = '/explorer?existingChartQuery=%7B%22query%22%3A%22%22%2C%22startTimeMillis%22%3A1483235880940%2C%22endTimeMillis%22%3A1483235882142%2C%22piqlFunctionGroups%22%3A%5B%7B%22functions%22%3A%5B%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%5D%2C%22field%22%3Anull%7D%5D%2C%22dateFilterPreset%22%3A%22CUSTOM%22%2C%22shouldGroupByTime%22%3Atrue%2C%22eventSortOrder%22%3A%22DESC%22%2C%22summarySortOrder%22%3A%22DESC%22%2C%22compareQueryOrderBy%22%3A%22TREND%22%2C%22compareQuerySortOrder%22%3A%22DESC%22%2C%22compareQueryOptions%22%3Anull%2C%22messageViewType%22%3A%22EVENTS%22%2C%22constraintToggle%22%3A%22ALL%22%2C%22piqlFunction%22%3A%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%2C%22piqlFunctionField%22%3Anull%2C%22fieldConstraints%22%3A%5B%5D%2C%22supplementalConstraints%22%3A%5B%5D%2C%22groupByFields%22%3A%5B%5D%2C%22extractedFields%22%3A%5B%5D%7D&chartOptions=%7B%22logaxis%22%3Afalse%2C%22spline%22%3Afalse%7D'


def test_parse_without_connections():
    root = ExplorerUrlParse(EXAMPLE_EXPLORER_URL)
    assert 1483235880940 == root.start

    qs = root.chartingurl_export(root.start, altend=root.end)


def test_retrieve_overview(ui):
    E = '/explorer/?existingChartQuery=%7B%22query%22%3A%22%22%2C%22startTimeMillis%22%3A1483154191149%2C%22endTimeMillis%22%3A1483568398919%2C%22piqlFunctionGroups%22%3A%5B%7B%22functions%22%3A%5B%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%5D%2C%22field%22%3Anull%7D%5D%2C%22dateFilterPreset%22%3A%22ALL_TIME%22%2C%22shouldGroupByTime%22%3Atrue%2C%22eventSortOrder%22%3A%22DESC%22%2C%22summarySortOrder%22%3A%22DESC%22%2C%22compareQueryOrderBy%22%3A%22TREND%22%2C%22compareQuerySortOrder%22%3A%22DESC%22%2C%22compareQueryOptions%22%3Anull%2C%22messageViewType%22%3A%22EVENTS%22%2C%22constraintToggle%22%3A%22ALL%22%2C%22piqlFunction%22%3A%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%2C%22piqlFunctionField%22%3Anull%2C%22fieldConstraints%22%3A%5B%5D%2C%22supplementalConstraints%22%3A%5B%5D%2C%22groupByFields%22%3A%5B%5D%2C%22extractedFields%22%3A%5B%5D%7D&chartOptions=%7B%22logaxis%22%3Afalse%2C%22spline%22%3Afalse%7D'

    root = ExplorerUrlParse(E)

    generated_url = root.chartingurl_export(root.start, altend=root.end)

    a = AggregateQuery(ui, generated_url)

    assert 0 < len(a.bins) < 20
    assert a.bins[0][0] <= a.bins[0][1]
