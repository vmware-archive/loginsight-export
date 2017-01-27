from urllib.parse import parse_qs
from requests.utils import urlparse
import pytest

from loginsightexport.paramhelper import ExplorerUrlParse

"""Convert UI explorer/share URLs to paramsHelper models for Export. Does not make network connections."""


def explode_url_components(url, expecteddifferentfields = ["paramsHelper.clientNowMillis", "downloadToken", "exportHelper.exportToken"]):
    """Helper function consumes a url, with or without scheme/hostname, and returns a dictionary for the query-component"""

    p = urlparse(url)
    d = parse_qs(p.query)

    r = {}
    for _ in d:
        if _ in expecteddifferentfields:  # These fields are going to be different for every request, but we want to know that it was present.
            r[_] = "ignored.{0}".format(_)  # Set to a dummy value containing the field name
        else:
            r[_] = d[_]
    return r


def diff_url_components(a, b):
    """Helper function that compares two URLs by their exploded dict representations"""
    assert explode_url_components(a) == explode_url_components(b)


@pytest.mark.xfail(reason="Need to correct existingMessageQuery")
def test_extracted_fields_export_events():
    u = '/explorer/?existingChartQuery=%7B%22query%22%3A%22query%20text%22%2C%22startTimeMillis%22%3A1479275107728%2C%22endTimeMillis%22%3A1479280737437%2C%22piqlFunctionGroups%22%3A%5B%7B%22functions%22%3A%5B%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%5D%2C%22field%22%3Anull%7D%5D%2C%22dateFilterPreset%22%3A%22CUSTOM%22%2C%22shouldGroupByTime%22%3Atrue%2C%22eventSortOrder%22%3A%22DESC%22%2C%22summarySortOrder%22%3A%22DESC%22%2C%22compareQueryOrderBy%22%3A%22TREND%22%2C%22compareQuerySortOrder%22%3A%22DESC%22%2C%22compareQueryOptions%22%3Anull%2C%22messageViewType%22%3A%22EVENTS%22%2C%22constraintToggle%22%3A%22ALL%22%2C%22piqlFunction%22%3A%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%2C%22piqlFunctionField%22%3Anull%2C%22fieldConstraints%22%3A%5B%7B%22internalName%22%3A%22text%22%2C%22operator%22%3A%22DOES_NOT_CONTAIN%22%2C%22value%22%3A%22doesntcontainthis%22%7D%2C%7B%22internalName%22%3A%22__li_source_path%22%2C%22operator%22%3A%22DOES_NOT_CONTAIN%22%2C%22value%22%3A%22sourcefake%22%7D%2C%7B%22internalName%22%3A%22java_thread%22%2C%22operator%22%3A%22EXISTS%22%2C%22value%22%3A%22logsearchworker-thread-1272%22%7D%2C%7B%22internalName%22%3A%22node_address%22%2C%22operator%22%3A%22CONTAINS%22%2C%22value%22%3A%2210.145.133.123%22%7D%2C%7B%22internalName%22%3A%22ibadax3un5vwk3tomfwwk000%22%2C%22operator%22%3A%22CONTAINS%22%2C%22value%22%3A%22178342c5c4139eca%22%7D%5D%2C%22supplementalConstraints%22%3A%5B%5D%2C%22groupByFields%22%3A%5B%5D%2C%22extractedFields%22%3A%5B%7B%22displayName%22%3A%22tokenname%22%2C%22preContext%22%3A%22token%3D%22%2C%22postContext%22%3A%22%5C%5C%5D%22%2C%22regexValue%22%3A%22%5BA-Fa-f0-9%5D%2B%22%2C%22internalName%22%3A%22ibadax3un5vwk3tomfwwk000%22%2C%22constraints%22%3Anull%7D%5D%7D&chartOptions=%7B%22logaxis%22%3Afalse%2C%22spline%22%3Afalse%7D'
    m = '/messages?exportHelper.exportToken=1483131202866&exportHelper.exportFormat=JSON&export=true&existingMessageQuery=%7B%22query%22%3A%22query%20text%22%2C%22startTimeMillis%22%3A1479275107728%2C%22endTimeMillis%22%3A1479280737437%2C%22piqlFunctionGroups%22%3A%5B%7B%22functions%22%3A%5B%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%5D%2C%22field%22%3Anull%7D%5D%2C%22dateFilterPreset%22%3A%22CUSTOM%22%2C%22shouldGroupByTime%22%3Atrue%2C%22eventSortOrder%22%3A%22DESC%22%2C%22summarySortOrder%22%3A%22DESC%22%2C%22compareQueryOrderBy%22%3A%22TREND%22%2C%22compareQuerySortOrder%22%3A%22DESC%22%2C%22compareQueryOptions%22%3Anull%2C%22messageViewType%22%3A%22EVENTS%22%2C%22constraintToggle%22%3A%22ALL%22%2C%22piqlFunction%22%3A%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%2C%22piqlFunctionField%22%3Anull%2C%22fieldConstraints%22%3A%5B%7B%22internalName%22%3A%22text%22%2C%22operator%22%3A%22DOES_NOT_CONTAIN%22%2C%22value%22%3A%22doesntcontainthis%22%7D%2C%7B%22internalName%22%3A%22__li_source_path%22%2C%22operator%22%3A%22DOES_NOT_CONTAIN%22%2C%22value%22%3A%22sourcefake%22%7D%2C%7B%22internalName%22%3A%22java_thread%22%2C%22operator%22%3A%22EXISTS%22%2C%22value%22%3A%22logsearchworker-thread-1272%22%7D%2C%7B%22internalName%22%3A%22node_address%22%2C%22operator%22%3A%22CONTAINS%22%2C%22value%22%3A%2210.145.133.123%22%7D%2C%7B%22internalName%22%3A%22ibadax3un5vwk3tomfwwk000%22%2C%22operator%22%3A%22CONTAINS%22%2C%22value%22%3A%22178342c5c4139eca%22%7D%5D%2C%22supplementalConstraints%22%3A%5B%5D%2C%22groupByFields%22%3A%5B%5D%2C%22extractedFields%22%3A%5B%7B%22displayName%22%3A%22tokenname%22%2C%22preContext%22%3A%22token%3D%22%2C%22postContext%22%3A%22%5C%5C%5D%22%2C%22regexValue%22%3A%22%5BA-Fa-f0-9%5D%2B%22%2C%22internalName%22%3A%22ibadax3un5vwk3tomfwwk000%22%2C%22constraints%22%3Anull%7D%5D%7D&resultTo=20000&downloadToken=1483131202866'

    o = ExplorerUrlParse(u)

    proposed_messages = str(o.messagesurl_export(outputformat="JSON"))
    diff_url_components(m, proposed_messages)

def test_extracted_fields_export_chart():
    u = '/explorer/?existingChartQuery=%7B%22query%22%3A%22query%20text%22%2C%22startTimeMillis%22%3A1479275107728%2C%22endTimeMillis%22%3A1479280737437%2C%22piqlFunctionGroups%22%3A%5B%7B%22functions%22%3A%5B%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%5D%2C%22field%22%3Anull%7D%5D%2C%22dateFilterPreset%22%3A%22CUSTOM%22%2C%22shouldGroupByTime%22%3Atrue%2C%22eventSortOrder%22%3A%22DESC%22%2C%22summarySortOrder%22%3A%22DESC%22%2C%22compareQueryOrderBy%22%3A%22TREND%22%2C%22compareQuerySortOrder%22%3A%22DESC%22%2C%22compareQueryOptions%22%3Anull%2C%22messageViewType%22%3A%22EVENTS%22%2C%22constraintToggle%22%3A%22ALL%22%2C%22piqlFunction%22%3A%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%2C%22piqlFunctionField%22%3Anull%2C%22fieldConstraints%22%3A%5B%7B%22internalName%22%3A%22text%22%2C%22operator%22%3A%22DOES_NOT_CONTAIN%22%2C%22value%22%3A%22doesntcontainthis%22%7D%2C%7B%22internalName%22%3A%22__li_source_path%22%2C%22operator%22%3A%22DOES_NOT_CONTAIN%22%2C%22value%22%3A%22sourcefake%22%7D%2C%7B%22internalName%22%3A%22java_thread%22%2C%22operator%22%3A%22EXISTS%22%2C%22value%22%3A%22logsearchworker-thread-1272%22%7D%2C%7B%22internalName%22%3A%22node_address%22%2C%22operator%22%3A%22CONTAINS%22%2C%22value%22%3A%2210.145.133.123%22%7D%2C%7B%22internalName%22%3A%22ibadax3un5vwk3tomfwwk000%22%2C%22operator%22%3A%22CONTAINS%22%2C%22value%22%3A%22178342c5c4139eca%22%7D%5D%2C%22supplementalConstraints%22%3A%5B%5D%2C%22groupByFields%22%3A%5B%5D%2C%22extractedFields%22%3A%5B%7B%22displayName%22%3A%22tokenname%22%2C%22preContext%22%3A%22token%3D%22%2C%22postContext%22%3A%22%5C%5C%5D%22%2C%22regexValue%22%3A%22%5BA-Fa-f0-9%5D%2B%22%2C%22internalName%22%3A%22ibadax3un5vwk3tomfwwk000%22%2C%22constraints%22%3Anull%7D%5D%7D&chartOptions=%7B%22logaxis%22%3Afalse%2C%22spline%22%3Afalse%7D'
    c = '/logcharting?exportHelper.exportToken=1483131252550&exportHelper.exportFormat=JSON&export=true&paramsHelper.startTimeMillis=1479275107728&paramsHelper.endTimeMillis=1479280737437&paramsHelper.dateFilterPreset=CUSTOM&paramsHelper.query=query%20text&paramsHelper.eventSortOrder=DESC&paramsHelper.summarySortOrder=DESC&paramsHelper.compareQuerySortOrder=DESC&paramsHelper.compareQueryOrderBy=TREND&paramsHelper.constraintToggle=ALL&paramsHelper.clientNowMillis=1483131068107&paramsHelper.messageViewType=EVENTS&paramsHelper.funcGroups%5B0%5D.piqlFunctions%5B0%5D=COUNT&paramsHelper.shouldGroupByTime=true&paramsHelper.fieldConstraints%5B0%5D.internalName=text&paramsHelper.fieldConstraints%5B0%5D.value=doesntcontainthis&paramsHelper.fieldConstraints%5B0%5D.operator=DOES_NOT_CONTAIN&paramsHelper.fieldConstraints%5B1%5D.internalName=__li_source_path&paramsHelper.fieldConstraints%5B1%5D.value=sourcefake&paramsHelper.fieldConstraints%5B1%5D.operator=DOES_NOT_CONTAIN&paramsHelper.fieldConstraints%5B2%5D.internalName=java_thread&paramsHelper.fieldConstraints%5B2%5D.value=logsearchworker-thread-1272&paramsHelper.fieldConstraints%5B2%5D.operator=EXISTS&paramsHelper.fieldConstraints%5B3%5D.internalName=node_address&paramsHelper.fieldConstraints%5B3%5D.value=10.145.133.123&paramsHelper.fieldConstraints%5B3%5D.operator=CONTAINS&paramsHelper.fieldConstraints%5B4%5D.internalName=ibadax3un5vwk3tomfwwk000&paramsHelper.fieldConstraints%5B4%5D.value=178342c5c4139eca&paramsHelper.fieldConstraints%5B4%5D.operator=CONTAINS&downloadToken=1483131252551'

    o = ExplorerUrlParse(u)

    proposed_charting = str(o.chartingurl_export())
    diff_url_components(c, proposed_charting)
