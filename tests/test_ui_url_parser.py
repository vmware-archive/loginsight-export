# -*- coding: utf-8 -*-

import pytest

from loginsightexport.compat import parse_qs, urlparse
from loginsightexport.paramhelper import ExplorerUrlParse


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


"""Convert UI explorer/share URLs to paramsHelper models. Does not make network connections."""

pytestmark = pytest.mark.skip("This is an unused non-export interface")


def explode_query_params(querystring):
    """Consumes a x=y&foo=bar query string, and emits a dictionary with some keys ignored"""
    expected_different = ["paramsHelper.clientNowMillis", "downloadToken", "exportHelper.exportToken"]
    d = parse_qs(querystring)

    r = {}
    for _ in d:
        if _ in expected_different:  # These fields are going to be different for every request, but we want to know that it was present.
            r[_] = "ignored.{0}".format(_)  # Set to a dummy value containing the field name
        else:
            r[_] = d[_]
    return r


def explode_url_components(url):
    """Consumes a url, with or without scheme/hostname, and returns a dictionary for the query-component"""
    p = urlparse(url)
    return explode_query_params(p.query)


def diff_url_components(a, b):
    assert explode_url_components(a) == explode_url_components(b)


def compare_url_tuple(user_url, messages_gold, logcharting_gold):
    o = ExplorerUrlParse(user_url)

    proposed_messages = str(o.messagesurl)
    diff_url_components(messages_gold, proposed_messages)

    proposed_charting = str(o.chartingurl)
    diff_url_components(logcharting_gold, proposed_charting)


def test_simple_query():
    # Convert A into B and C
    u = "https://lol.licf.vmware.com/explorer/?existingChartQuery=%7B%22query%22%3A%22%22%2C%22startTimeMillis%22%3A1470051706664%2C%22endTimeMillis%22%3A1479269917713%2C%22piqlFunctionGroups%22%3A%5B%7B%22functions%22%3A%5B%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%5D%2C%22field%22%3Anull%7D%5D%2C%22dateFilterPreset%22%3A%22CUSTOM%22%2C%22shouldGroupByTime%22%3Atrue%2C%22eventSortOrder%22%3A%22DESC%22%2C%22summarySortOrder%22%3A%22DESC%22%2C%22compareQueryOrderBy%22%3A%22TREND%22%2C%22compareQuerySortOrder%22%3A%22DESC%22%2C%22compareQueryOptions%22%3Anull%2C%22messageViewType%22%3A%22EVENTS%22%2C%22constraintToggle%22%3A%22ALL%22%2C%22piqlFunction%22%3A%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%2C%22piqlFunctionField%22%3Anull%2C%22fieldConstraints%22%3A%5B%5D%2C%22supplementalConstraints%22%3A%5B%5D%2C%22groupByFields%22%3A%5B%5D%2C%22extractedFields%22%3A%5B%5D%7D&chartOptions=%7B%22logaxis%22%3Afalse%2C%22spline%22%3Afalse%7D"
    m = "https://lol.licf.vmware.com/messages?paramsHelper.startTimeMillis=1470051706664&paramsHelper.endTimeMillis=1479269917713&paramsHelper.dateFilterPreset=CUSTOM&paramsHelper.query=&paramsHelper.eventSortOrder=DESC&paramsHelper.summarySortOrder=DESC&paramsHelper.compareQuerySortOrder=DESC&paramsHelper.compareQueryOrderBy=TREND&paramsHelper.constraintToggle=ALL&paramsHelper.clientNowMillis=1479269489283&paramsHelper.messageViewType=EVENTS&paramsHelper.funcGroups%5B0%5D.piqlFunctions%5B0%5D=COUNT&paramsHelper.shouldGroupByTime=true&search=true"
    c = "https://lol.licf.vmware.com/logcharting?paramsHelper.startTimeMillis=1470051706664&paramsHelper.endTimeMillis=1479269917713&paramsHelper.dateFilterPreset=CUSTOM&paramsHelper.query=&paramsHelper.eventSortOrder=DESC&paramsHelper.summarySortOrder=DESC&paramsHelper.compareQuerySortOrder=DESC&paramsHelper.compareQueryOrderBy=TREND&paramsHelper.constraintToggle=ALL&paramsHelper.clientNowMillis=1479269489283&paramsHelper.messageViewType=EVENTS&paramsHelper.funcGroups%5B0%5D.piqlFunctions%5B0%5D=COUNT&paramsHelper.shouldGroupByTime=true&generateMainChart=true"
    compare_url_tuple(u, m, c)


def test_compound_query():
    u = 'https://lol.licf.vmware.com/explorer/?existingChartQuery=%7B%22query%22%3A%22query%20text%22%2C%22startTimeMillis%22%3A1479186000000%2C%22endTimeMillis%22%3A1479277577258%2C%22piqlFunctionGroups%22%3A%5B%7B%22functions%22%3A%5B%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%5D%2C%22field%22%3Anull%7D%5D%2C%22dateFilterPreset%22%3A%22CUSTOM%22%2C%22shouldGroupByTime%22%3Atrue%2C%22eventSortOrder%22%3A%22DESC%22%2C%22summarySortOrder%22%3A%22DESC%22%2C%22compareQueryOrderBy%22%3A%22TREND%22%2C%22compareQuerySortOrder%22%3A%22DESC%22%2C%22compareQueryOptions%22%3Anull%2C%22messageViewType%22%3A%22EVENTS%22%2C%22constraintToggle%22%3A%22ALL%22%2C%22piqlFunction%22%3A%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%2C%22piqlFunctionField%22%3Anull%2C%22fieldConstraints%22%3A%5B%7B%22internalName%22%3A%22text%22%2C%22operator%22%3A%22DOES_NOT_CONTAIN%22%2C%22value%22%3A%22doesntcontainthis%22%7D%2C%7B%22internalName%22%3A%22__li_source_path%22%2C%22operator%22%3A%22DOES_NOT_CONTAIN%22%2C%22value%22%3A%22sourcefake%22%7D%2C%7B%22internalName%22%3A%22java_thread%22%2C%22operator%22%3A%22EXISTS%22%2C%22value%22%3A%22logsearchworker-thread-1272%22%7D%2C%7B%22internalName%22%3A%22node_address%22%2C%22operator%22%3A%22CONTAINS%22%2C%22value%22%3A%2210.145.133.123%22%7D%5D%2C%22supplementalConstraints%22%3A%5B%5D%2C%22groupByFields%22%3A%5B%5D%2C%22extractedFields%22%3A%5B%5D%7D&chartOptions=%7B%22logaxis%22%3Afalse%2C%22spline%22%3Afalse%7D'
    m = 'https://lol.licf.vmware.com/messages?paramsHelper.startTimeMillis=1479186000000&paramsHelper.endTimeMillis=1479277577258&paramsHelper.dateFilterPreset=CUSTOM&paramsHelper.query=query%20text&paramsHelper.eventSortOrder=DESC&paramsHelper.summarySortOrder=DESC&paramsHelper.compareQuerySortOrder=DESC&paramsHelper.compareQueryOrderBy=TREND&paramsHelper.constraintToggle=ALL&paramsHelper.clientNowMillis=1479275659978&paramsHelper.messageViewType=EVENTS&paramsHelper.funcGroups%5B0%5D.piqlFunctions%5B0%5D=COUNT&paramsHelper.shouldGroupByTime=true&paramsHelper.fieldConstraints%5B0%5D.internalName=text&paramsHelper.fieldConstraints%5B0%5D.value=doesntcontainthis&paramsHelper.fieldConstraints%5B0%5D.operator=DOES_NOT_CONTAIN&paramsHelper.fieldConstraints%5B1%5D.internalName=__li_source_path&paramsHelper.fieldConstraints%5B1%5D.value=sourcefake&paramsHelper.fieldConstraints%5B1%5D.operator=DOES_NOT_CONTAIN&paramsHelper.fieldConstraints%5B2%5D.internalName=java_thread&paramsHelper.fieldConstraints%5B2%5D.value=logsearchworker-thread-1272&paramsHelper.fieldConstraints%5B2%5D.operator=EXISTS&paramsHelper.fieldConstraints%5B3%5D.internalName=node_address&paramsHelper.fieldConstraints%5B3%5D.value=10.145.133.123&paramsHelper.fieldConstraints%5B3%5D.operator=CONTAINS&search=true'
    c = 'https://lol.licf.vmware.com/logcharting?paramsHelper.startTimeMillis=1479186000000&paramsHelper.endTimeMillis=1479277577258&paramsHelper.dateFilterPreset=CUSTOM&paramsHelper.query=query%20text&paramsHelper.eventSortOrder=DESC&paramsHelper.summarySortOrder=DESC&paramsHelper.compareQuerySortOrder=DESC&paramsHelper.compareQueryOrderBy=TREND&paramsHelper.constraintToggle=ALL&paramsHelper.clientNowMillis=1479275659978&paramsHelper.messageViewType=EVENTS&paramsHelper.funcGroups%5B0%5D.piqlFunctions%5B0%5D=COUNT&paramsHelper.shouldGroupByTime=true&paramsHelper.fieldConstraints%5B0%5D.internalName=text&paramsHelper.fieldConstraints%5B0%5D.value=doesntcontainthis&paramsHelper.fieldConstraints%5B0%5D.operator=DOES_NOT_CONTAIN&paramsHelper.fieldConstraints%5B1%5D.internalName=__li_source_path&paramsHelper.fieldConstraints%5B1%5D.value=sourcefake&paramsHelper.fieldConstraints%5B1%5D.operator=DOES_NOT_CONTAIN&paramsHelper.fieldConstraints%5B2%5D.internalName=java_thread&paramsHelper.fieldConstraints%5B2%5D.value=logsearchworker-thread-1272&paramsHelper.fieldConstraints%5B2%5D.operator=EXISTS&paramsHelper.fieldConstraints%5B3%5D.internalName=node_address&paramsHelper.fieldConstraints%5B3%5D.value=10.145.133.123&paramsHelper.fieldConstraints%5B3%5D.operator=CONTAINS&generateMainChart=true'
    compare_url_tuple(u, m, c)


def test_extracted_fields():
    u = 'https://lol.licf.vmware.com/explorer?existingChartQuery=%7B%22query%22%3A%22query%20text%22%2C%22startTimeMillis%22%3A1479186000000%2C%22endTimeMillis%22%3A1479277577258%2C%22piqlFunctionGroups%22%3A%5B%7B%22functions%22%3A%5B%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%5D%2C%22field%22%3Anull%7D%5D%2C%22dateFilterPreset%22%3A%22CUSTOM%22%2C%22shouldGroupByTime%22%3Atrue%2C%22eventSortOrder%22%3A%22DESC%22%2C%22summarySortOrder%22%3A%22DESC%22%2C%22compareQueryOrderBy%22%3A%22TREND%22%2C%22compareQuerySortOrder%22%3A%22DESC%22%2C%22compareQueryOptions%22%3Anull%2C%22messageViewType%22%3A%22EVENTS%22%2C%22constraintToggle%22%3A%22ALL%22%2C%22piqlFunction%22%3A%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%2C%22piqlFunctionField%22%3Anull%2C%22fieldConstraints%22%3A%5B%7B%22internalName%22%3A%22text%22%2C%22operator%22%3A%22DOES_NOT_CONTAIN%22%2C%22value%22%3A%22doesntcontainthis%22%7D%2C%7B%22internalName%22%3A%22__li_source_path%22%2C%22operator%22%3A%22DOES_NOT_CONTAIN%22%2C%22value%22%3A%22sourcefake%22%7D%2C%7B%22internalName%22%3A%22java_thread%22%2C%22operator%22%3A%22EXISTS%22%2C%22value%22%3A%22logsearchworker-thread-1272%22%7D%2C%7B%22internalName%22%3A%22node_address%22%2C%22operator%22%3A%22CONTAINS%22%2C%22value%22%3A%2210.145.133.123%22%7D%2C%7B%22internalName%22%3A%22ibadax3un5vwk3tomfwwk000%22%2C%22operator%22%3A%22CONTAINS%22%2C%22value%22%3A%22178342c5c4139eca%22%7D%5D%2C%22supplementalConstraints%22%3A%5B%5D%2C%22groupByFields%22%3A%5B%5D%2C%22extractedFields%22%3A%5B%7B%22displayName%22%3A%22tokenname%22%2C%22preContext%22%3A%22token%3D%22%2C%22postContext%22%3A%22%5C%5C%5D%22%2C%22regexValue%22%3A%22%5BA-Fa-f0-9%5D%2B%22%2C%22internalName%22%3A%22ibadax3un5vwk3tomfwwk000%22%2C%22constraints%22%3Anull%7D%5D%7D&chartOptions=%7B%22logaxis%22%3Afalse%2C%22spline%22%3Afalse%7D'
    m = 'https://lol.licf.vmware.com/messages?paramsHelper.startTimeMillis=1479186000000&paramsHelper.endTimeMillis=1479277577258&paramsHelper.dateFilterPreset=CUSTOM&paramsHelper.query=query%20text&paramsHelper.eventSortOrder=DESC&paramsHelper.summarySortOrder=DESC&paramsHelper.compareQuerySortOrder=DESC&paramsHelper.compareQueryOrderBy=TREND&paramsHelper.constraintToggle=ALL&paramsHelper.clientNowMillis=1479326448555&paramsHelper.messageViewType=EVENTS&paramsHelper.funcGroups%5B0%5D.piqlFunctions%5B0%5D=COUNT&paramsHelper.shouldGroupByTime=true&paramsHelper.fieldConstraints%5B0%5D.internalName=text&paramsHelper.fieldConstraints%5B0%5D.value=doesntcontainthis&paramsHelper.fieldConstraints%5B0%5D.operator=DOES_NOT_CONTAIN&paramsHelper.fieldConstraints%5B1%5D.internalName=__li_source_path&paramsHelper.fieldConstraints%5B1%5D.value=sourcefake&paramsHelper.fieldConstraints%5B1%5D.operator=DOES_NOT_CONTAIN&paramsHelper.fieldConstraints%5B2%5D.internalName=java_thread&paramsHelper.fieldConstraints%5B2%5D.value=logsearchworker-thread-1272&paramsHelper.fieldConstraints%5B2%5D.operator=EXISTS&paramsHelper.fieldConstraints%5B3%5D.internalName=node_address&paramsHelper.fieldConstraints%5B3%5D.value=10.145.133.123&paramsHelper.fieldConstraints%5B3%5D.operator=CONTAINS&paramsHelper.fieldConstraints%5B4%5D.internalName=ibadax3un5vwk3tomfwwk000&paramsHelper.fieldConstraints%5B4%5D.value=178342c5c4139eca&paramsHelper.fieldConstraints%5B4%5D.operator=CONTAINS&search=true'
    c = 'https://lol.licf.vmware.com/logcharting?paramsHelper.startTimeMillis=1479186000000&paramsHelper.endTimeMillis=1479277577258&paramsHelper.dateFilterPreset=CUSTOM&paramsHelper.query=query%20text&paramsHelper.eventSortOrder=DESC&paramsHelper.summarySortOrder=DESC&paramsHelper.compareQuerySortOrder=DESC&paramsHelper.compareQueryOrderBy=TREND&paramsHelper.constraintToggle=ALL&paramsHelper.clientNowMillis=1479326448555&paramsHelper.messageViewType=EVENTS&paramsHelper.funcGroups%5B0%5D.piqlFunctions%5B0%5D=COUNT&paramsHelper.shouldGroupByTime=true&paramsHelper.fieldConstraints%5B0%5D.internalName=text&paramsHelper.fieldConstraints%5B0%5D.value=doesntcontainthis&paramsHelper.fieldConstraints%5B0%5D.operator=DOES_NOT_CONTAIN&paramsHelper.fieldConstraints%5B1%5D.internalName=__li_source_path&paramsHelper.fieldConstraints%5B1%5D.value=sourcefake&paramsHelper.fieldConstraints%5B1%5D.operator=DOES_NOT_CONTAIN&paramsHelper.fieldConstraints%5B2%5D.internalName=java_thread&paramsHelper.fieldConstraints%5B2%5D.value=logsearchworker-thread-1272&paramsHelper.fieldConstraints%5B2%5D.operator=EXISTS&paramsHelper.fieldConstraints%5B3%5D.internalName=node_address&paramsHelper.fieldConstraints%5B3%5D.value=10.145.133.123&paramsHelper.fieldConstraints%5B3%5D.operator=CONTAINS&paramsHelper.fieldConstraints%5B4%5D.internalName=ibadax3un5vwk3tomfwwk000&paramsHelper.fieldConstraints%5B4%5D.value=178342c5c4139eca&paramsHelper.fieldConstraints%5B4%5D.operator=CONTAINS&generateMainChart=true'
    compare_url_tuple(u, m, c)


def test_all_time_query():
    u = 'https://lol.licf.vmware.com/explorer?existingChartQuery=%7B%22query%22%3A%22%22%2C%22startTimeMillis%22%3A1470298981525%2C%22endTimeMillis%22%3A1479437345211%2C%22piqlFunctionGroups%22%3A%5B%7B%22functions%22%3A%5B%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%5D%2C%22field%22%3Anull%7D%5D%2C%22dateFilterPreset%22%3A%22CUSTOM%22%2C%22shouldGroupByTime%22%3Atrue%2C%22eventSortOrder%22%3A%22DESC%22%2C%22summarySortOrder%22%3A%22DESC%22%2C%22compareQueryOrderBy%22%3A%22TREND%22%2C%22compareQuerySortOrder%22%3A%22DESC%22%2C%22compareQueryOptions%22%3Anull%2C%22messageViewType%22%3A%22EVENTS%22%2C%22constraintToggle%22%3A%22ALL%22%2C%22piqlFunction%22%3A%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%2C%22piqlFunctionField%22%3Anull%2C%22fieldConstraints%22%3A%5B%5D%2C%22supplementalConstraints%22%3A%5B%5D%2C%22groupByFields%22%3A%5B%5D%2C%22extractedFields%22%3A%5B%5D%7D&chartOptions=%7B%22logaxis%22%3Afalse%2C%22spline%22%3Afalse%7D'
    m = 'https://lol.licf.vmware.com/messages?paramsHelper.startTimeMillis=1470298981525&paramsHelper.endTimeMillis=1479437345211&paramsHelper.dateFilterPreset=CUSTOM&paramsHelper.query=&paramsHelper.eventSortOrder=DESC&paramsHelper.summarySortOrder=DESC&paramsHelper.compareQuerySortOrder=DESC&paramsHelper.compareQueryOrderBy=TREND&paramsHelper.constraintToggle=ALL&paramsHelper.clientNowMillis=1479436983592&paramsHelper.messageViewType=EVENTS&paramsHelper.funcGroups%5B0%5D.piqlFunctions%5B0%5D=COUNT&paramsHelper.shouldGroupByTime=true&search=true'
    c = 'https://lol.licf.vmware.com/logcharting?paramsHelper.startTimeMillis=1470298981525&paramsHelper.endTimeMillis=1479437345211&paramsHelper.dateFilterPreset=CUSTOM&paramsHelper.query=&paramsHelper.eventSortOrder=DESC&paramsHelper.summarySortOrder=DESC&paramsHelper.compareQuerySortOrder=DESC&paramsHelper.compareQueryOrderBy=TREND&paramsHelper.constraintToggle=ALL&paramsHelper.clientNowMillis=1479436983592&paramsHelper.messageViewType=EVENTS&paramsHelper.funcGroups%5B0%5D.piqlFunctions%5B0%5D=COUNT&paramsHelper.shouldGroupByTime=true&generateMainChart=true'
    compare_url_tuple(u, m, c)
