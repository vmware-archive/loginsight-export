# -*- coding: utf-8 -*-

from loginsightexport.paramhelper import ExplorerUrlParse
from loginsightexport.uidriver import AggregateQuery

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


def test_bug_15(ui):
    """
    Verify bug 15, where reading innerlistitem['value'] failed with TypeError
    >>> params['paramsHelper.%s[%d].piqlFunctions[%d]' % (insertedkey, counter, second_counter)] = innerlistitem['value']
    TypeError: string indices must be integers
    """
    u = "/explorer/?existingChartQuery=%7B%22query%22%3A%22%22%2C%22startTimeMillis%22%3A1510249336717%2C%22endTimeMillis%22%3A1510250503304%2C%22piqlFunctionGroups%22%3A%5B%7B%22functions%22%3A%5B%7B%22label%22%3A%22Unique%20count%22%2C%22value%22%3A%22UCOUNT%22%2C%22requiresField%22%3Atrue%2C%22numericOnly%22%3Afalse%7D%5D%2C%22field%22%3A%7B%22internalName%22%3A%22event_type%22%2C%22displayName%22%3A%22event_type%22%2C%22displayNamespace%22%3Anull%7D%7D%2C%7B%22functions%22%3A%5B%7B%22label%22%3A%22Count%22%2C%22value%22%3A%22COUNT%22%2C%22requiresField%22%3Afalse%2C%22numericOnly%22%3Afalse%7D%5D%2C%22field%22%3Anull%7D%5D%2C%22dateFilterPreset%22%3A%22ALL_TIME%22%2C%22shouldGroupByTime%22%3Atrue%2C%22eventSortOrder%22%3A%22DESC%22%2C%22summarySortOrder%22%3A%22DESC%22%2C%22compareQueryOrderBy%22%3A%22TREND%22%2C%22compareQuerySortOrder%22%3A%22DESC%22%2C%22compareQueryOptions%22%3Anull%2C%22messageViewType%22%3A%22EVENTS%22%2C%22constraintToggle%22%3A%22ALL%22%2C%22piqlFunction%22%3A%7B%22label%22%3A%22Unique%20count%22%2C%22value%22%3A%22UCOUNT%22%2C%22requiresField%22%3Atrue%2C%22numericOnly%22%3Afalse%7D%2C%22piqlFunctionField%22%3A%22event_type%22%2C%22fieldConstraints%22%3A%5B%5D%2C%22supplementalConstraints%22%3A%5B%5D%2C%22groupByFields%22%3A%5B%7B%22displayName%22%3A%22source%22%2C%22internalName%22%3A%22__li_source_path%22%2C%22displayNamespace%22%3Anull%2C%22numericGroupByType%22%3A%22EACH_VALUE%22%2C%22numericGroupByValue%22%3Anull%7D%2C%7B%22displayName%22%3A%22hostname%22%2C%22internalName%22%3A%22hostname%22%2C%22displayNamespace%22%3Anull%2C%22numericGroupByType%22%3A%22EACH_VALUE%22%2C%22numericGroupByValue%22%3Anull%7D%5D%2C%22extractedFields%22%3A%5B%5D%7D&chartOptions=%7B%22logaxis%22%3Afalse%2C%22legend%22%3Atrue%2C%22stacking%22%3A%22normal%22%7D"

    root = ExplorerUrlParse(u)

    generated_url = root.chartingurl_export(root.start, altend=root.end)

    a = AggregateQuery(ui, generated_url)
