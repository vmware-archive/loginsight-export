import requests_mock
from collections import Counter
import json
import logging
import re
import pytest
from itertools import zip_longest, groupby, count


from .utils import RandomDict, requiresauthentication

from loginsightexport.compat import parse_qs

logcharting_url_matcher = re.compile('/logcharting?(.*)$')
messages_url_matcher = re.compile('/messages?(.*)$')

mockserverlogger = logging.getLogger("LogInsightMockAdapter")


class Database(object):
    """Generate a corupus of log messages 'event nnnnn'"""
    def __init__(self, start=1483154000000, end=1483568999999):
        middle = (end+start)/2
        self.data = []
        for i in range(start, end, 500001):
            self.data.append((i, "event %d" % (i-1483154000000)))
            if i > middle:
                self.data.append((i+1, "event.1 %d" % (i - 1483154000000 - 1)))

    def results_in_range(self, start, end):
        for i, msg in self.data:
            if start <= i <= end:
                yield (i, msg)

    def query_chart(self, start, end, buckets=3):
        round_down_start = int(round(start/10000)*10000)
        offset = int((end-round_down_start)/(buckets+1)/1000)*1000

        bins_starts = list(range(round_down_start, end, offset))
        bins_ends = list(range(round_down_start + offset - 1, end + offset - 1, offset))

        def newbin(start, end):
            return {"groupByValues": [{'isTime': True, 'val': start, 'endVal': end}],
                    "aggregationValues": [0]}

        result_bins = {start: newbin(start, end) for start, end in zip(bins_starts, bins_ends)}

        iterable = self.results_in_range(start, end)

        def key_fn(args):
            x, y = args[0], args[1]
            return min([_ for _ in result_bins.keys() if _ >= x])

        for k, g in groupby(iterable, key=key_fn):
            result_bins[k]['aggregationValues'][0] += len(list(g))

        return [v for k, v in result_bins.items()]

    def query_events(self, start, end):
        pass


class MockedUIQueryMixin(requests_mock.Adapter):
    def __init__(self, **kwargs):
        super(MockedUIQueryMixin, self).__init__(**kwargs)
        self._case_sensitive = True

        self.licenses_known = RandomDict({'12345678-90ab-cdef-1234-567890abcdef': {'typeEnum': 'OSI', 'id': '12345678-90ab-cdef-1234-567890abcdef', 'error': '', 'status': 'Active',
                                                                                   'configuration': '1 Operating System Instance (OSI)',
                                                                                   'licenseKey': '4J2TK-XXXXX-XXXXX-XXXXX-XXXXX', 'infinite': True, 'count': 0, 'expiration': 0}})

        # License Keys
        self.register_uri('GET', messages_url_matcher, status_code=200, text=self.callback_get_messages)
        self.register_uri('GET', logcharting_url_matcher, status_code=200, text=self.callback_get_chart)

    @requiresauthentication
    def callback_get_messages(self, request, context, session_id, user_id):
        pass

    @requiresauthentication
    def callback_get_chart(self, request, context, session_id, user_id):
        query = request.qs
        assert query['exportHelper.exportFormat'] == ['JSON']
        assert query['export'] == ['true']

        start = int(query['paramsHelper.startTimeMillis'][0])
        end = int(query['paramsHelper.endTimeMillis'][0])

        assert 0 <= start <= end

        rows = [
                {'groupByValues': [{'isTime': True, 'val': 1483235882100, 'endVal': 1483235882199}], 'aggregationValues': [8653]},
                {'groupByValues': [{'isTime': True, 'val': 1483235882000, 'endVal': 1483235882099}], 'aggregationValues': [10939]},
                {'groupByValues': [{'isTime': True, 'val': 1483235881900, 'endVal': 1483235881999}], 'aggregationValues': [6344]},
                {'groupByValues': [{'isTime': True, 'val': 1483235881800, 'endVal': 1483235881899}], 'aggregationValues': [1848]},
                {'groupByValues': [{'isTime': True, 'val': 1483235881700, 'endVal': 1483235881799}], 'aggregationValues': [1791]},
                {'groupByValues': [{'isTime': True, 'val': 1483235881600, 'endVal': 1483235881699}], 'aggregationValues': [489]},
                {'groupByValues': [{'isTime': True, 'val': 1483235881500, 'endVal': 1483235881599}], 'aggregationValues': [462]},
                {'groupByValues': [{'isTime': True, 'val': 1483235881400, 'endVal': 1483235881499}], 'aggregationValues': [384]},
                {'groupByValues': [{'isTime': True, 'val': 1483235881300, 'endVal': 1483235881399}], 'aggregationValues': [986]},
                {'groupByValues': [{'isTime': True, 'val': 1483235881200, 'endVal': 1483235881299}], 'aggregationValues': [383]},
                {'groupByValues': [{'isTime': True, 'val': 1483235881100, 'endVal': 1483235881199}], 'aggregationValues': [319]},
                {'groupByValues': [{'isTime': True, 'val': 1483235881000, 'endVal': 1483235881099}], 'aggregationValues': [1410]},
                {'groupByValues': [{'isTime': True, 'val': 1483235880900, 'endVal': 1483235880999}], 'aggregationValues': [182]}
            ]

        d = Database()
        rows = d.query_chart(start, end)
        return json.dumps({
            'groupByHeaders': [{'displayNamespace': None, 'isTime': True, 'displayName': 'time', 'internalName': 'timestamp'}],
            'rows': rows,
            'aggregationHeaders': [{'func': 'COUNT', 'funcDisplayName': 'Count'}]
        })
