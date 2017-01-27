from urllib.parse import parse_qs
from requests.utils import urlparse

from loginsightexport.uidriver import AggregateQuery



def test_extracted_fields_export_chart():
    GROUPED_BY_TIME_AND_SOURCE = {'groupByHeaders': [{'displayName': 'time', 'internalName': 'timestamp', 'isTime': True, 'displayNamespace': None}, {'displayName': 'source', 'internalName': '__li_source_path', 'isTime': False, 'displayNamespace': None}], 'rows': [{'aggregationValues': [100], 'groupByValues': [{'val': 1483154100000, 'isTime': True, 'endVal': 1483154399999}, {'val': '192.168.50.1', 'tooltipVal': '192.168.50.1', 'fieldType': 'STRING', 'operator': 'CONTAINS'}]}], 'aggregationHeaders': [{'funcDisplayName': 'Count', 'func': 'COUNT'}]}
