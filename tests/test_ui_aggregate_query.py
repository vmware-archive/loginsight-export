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


def test_extracted_fields_export_chart():
    GROUPED_BY_TIME_AND_SOURCE = {'groupByHeaders': [{'displayName': 'time', 'internalName': 'timestamp', 'isTime': True, 'displayNamespace': None}, {'displayName': 'source', 'internalName': '__li_source_path', 'isTime': False, 'displayNamespace': None}], 'rows': [{'aggregationValues': [100], 'groupByValues': [{'val': 1483154100000, 'isTime': True, 'endVal': 1483154399999}, {'val': '192.168.50.1', 'tooltipVal': '192.168.50.1', 'fieldType': 'STRING', 'operator': 'CONTAINS'}]}], 'aggregationHeaders': [{'funcDisplayName': 'Count', 'func': 'COUNT'}]}
