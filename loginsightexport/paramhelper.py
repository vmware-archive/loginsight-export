# -*- coding: utf-8 -*-

import json
import logging
import time
import warnings
import functools

from urllib.parse import parse_qs, urlparse, urlencode


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


class SeenWarning(UserWarning):
    """Raised when a @once function is called multiple times with the same arguments."""
    def __init__(self, function_name, args, kwargs):
        self.function_name = function_name
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return '{s.function_name}({s.args}, {s.kwargs}) called multiple times'.format(s=self)


def once(func):
    """Decorator: Record function arguments, warn when a function is called multiple times identically."""
    func._seen_history = set()

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        k = str([args, kwargs])
        if k in func._seen_history:
            warnings.warn(SeenWarning(function_name=func.__name__, args=args, kwargs=kwargs))
        else:
            func._seen_history.add(k)
        return func(*args, **kwargs)
    return wrapper


class ExplorerUrlParse(object):
    """
    Extract query components from an /explorer?existingChartQuery=... url. Does not request the URL.
    Produces three elements, all of which are JSON embedeed in the original URL, and all of which are sparse
        - existingChartQuery - all the helperParams
        - timeWindowToggle - the "1 bar =" bin-width UI element, ignored
        - chartOptions - chart type and legend
    """

    def __init__(self, url):
        self.from_explorer_url(url)
        self.lasttoken = int(time.time()) * 1000

    def from_explorer_url(self, url):
        p = urlparse(url)

        self.scheme = p.scheme
        self.netloc = p.netloc

        query_string = p.query
        queries = parse_qs(query_string)

        def _parse_json_or_empty_dict(queries, s):
            try:
                return json.loads(queries[s][0])
            except:
                logger.debug("Cannot retrieve %s, returning {}" % s)
                return {}

        self.chartOptions = _parse_json_or_empty_dict(queries, 'chartOptions')
        self.timeWindowToggle = _parse_json_or_empty_dict(queries, 'timeWindowToggle')
        self.existingChartQuery = _parse_json_or_empty_dict(queries, 'existingChartQuery')
        self.existingChartQuery_raw = queries['existingChartQuery'][0]

    def currentTimeMillis(self):
        return int(round(time.time() * 1000))

    def getChartParamsHelper(self, extraparams={}):
        warnings.warn(DeprecationWarning("getChartParamsHelper shouldn't be used"))
        """Serialize back to a requests-friendly params dict"""
        token = int(time.time()) * 1000

        while token == self.lasttoken:
            token += 1
            logger.warning("getChartParamsHelper Token bump to {0} in {1}".format(token, id(self)))
        self.lasttoken = token

        params = {}
        if extraparams:
            params.update(extraparams)

        for _ in self.existingChartQuery:

            if _ == 'piqlFunctionGroups':
                insertedkey = 'funcGroups'
            else:
                insertedkey = _

            if self.existingChartQuery[_]:
                s = self.existingChartQuery[_]

                if isinstance(s, dict):
                    # params['paramsHelper.%s' % _] = json.dumps(s)
                    logger.info("Dropping parameter %s = %s" % (_, str(s)))

                elif isinstance(s, list):
                    logger.debug("Mapping list-of-dict item %s = %s" % (_, str(s)))

                    if _ in ["fieldConstraints", "extractedFields"]:
                        counter = 0
                        for listitem in s:
                            for fieldConstraintsDictKey in listitem:
                                params['paramsHelper.%s[%d].%s' % (insertedkey, counter, fieldConstraintsDictKey)] = \
                                    listitem[fieldConstraintsDictKey]
                            counter += 1
                    else:
                        counter = 0
                        for listitem in s:
                            for dictkey in listitem:
                                if listitem[dictkey]:
                                    second_counter = 0
                                    for innerlistitem in listitem[dictkey]:
                                        params['paramsHelper.%s[%d].piqlFunctions[%d]' % (insertedkey, counter, second_counter)] = innerlistitem['value']
                                        second_counter += 1
                            counter += 1

                elif _ == "paramsHelper.cancelToken":
                    logger.info("Dropping paramsHelper.cancelToken from model - should be generated at query-time")
                elif _ == "shouldGroupByTime":
                    params['paramsHelper.%s' % insertedkey] = str(s).lower()
                    logger.debug("Lowercase inserted %s = %s" % (insertedkey, str(s)))
                else:
                    params['paramsHelper.%s' % insertedkey] = str(s)
                    logger.debug("Direct inserted %s = %s" % (insertedkey, str(s)))
            else:
                if _ == "query":
                    params['paramsHelper.%s' % insertedkey] = ""
                    logger.debug("Inserted blank %s = ''" % (insertedkey))

        if 'export' in params:
            params['existingMessageQuery'] = self.existingChartQuery_raw

        return params

    def getExportEventsHelper(self, extraparams={}, altstart=None, altend=None, outputformat='JSON'):
        """Serialize back to a requests-friendly params dict"""
        token = int(time.time()) * 1000

        while token == self.lasttoken:
            token += 1
        self.lasttoken = token

        model = self.existingChartQuery.copy()

        if altstart and altend:
            logger.debug("Applied altstart {0} and altend {1}".format(altstart, altend))
            model['startTimeMillis'] = altstart
            model['endTimeMillis'] = altend
            model['dateFilterPreset'] = 'CUSTOM'
        params = {
            'export': 'true',
            'exportHelper.exportFormat': outputformat,
            'exportHelper.exportToken': token,
            'downloadToken': token,
            'resultTo': 20000,
            'existingMessageQuery': json.dumps(model)
        }
        if extraparams:
            params.update(extraparams)
        return params

    def getExportChartHelper(self, extraparams={}, altstart=None, altend=None):
        """Serialize back to a requests-friendly params dict"""
        token = int(time.time()) * 1000

        while token == self.lasttoken:
            token += 1
        self.lasttoken = token

        params = {}

        for _ in self.existingChartQuery:
            if _ == 'extractedFields':
                continue  # count-over-time charts don't need extracted fields.
            if _ == 'piqlFunctionGroups':
                insertedkey = 'funcGroups'
            else:
                insertedkey = _

            if self.existingChartQuery[_]:
                s = self.existingChartQuery[_]

                if isinstance(s, dict):
                    # params['paramsHelper.%s' % _] = json.dumps(s)
                    logger.debug("Skipping parameter %s = %s" % (_, str(s)))

                elif isinstance(s, list):
                    logger.debug("Mapping list-of-dict item %s = %s" % (_, str(s)))

                    if _ in ["fieldConstraints", "extractedFields", "groupByFields"]:
                        counter = 0
                        for listitem in s:
                            for fieldConstraintsDictKey in listitem:
                                params['paramsHelper.%s[%d].%s' % (insertedkey, counter, fieldConstraintsDictKey)] = \
                                    listitem[fieldConstraintsDictKey]
                            counter += 1
                    else:
                        counter = 0
                        for listitem in s:
                            for dictkey in listitem:
                                if listitem[dictkey]:
                                    second_counter = 0
                                    for innerlistitem in listitem[dictkey]:
                                        params['paramsHelper.%s[%d].piqlFunctions[%d]' % (insertedkey, counter, second_counter)] = innerlistitem['value']
                                        second_counter += 1
                            counter += 1

                elif _ == "paramsHelper.cancelToken":
                    logger.info("Dropping paramsHelper.cancelToken from model - should be generated at query-time")
                elif _ == "shouldGroupByTime":
                    params['paramsHelper.%s' % insertedkey] = str(s).lower()
                    logger.debug("Lowercase inserted %s = %s" % (insertedkey, str(s)))
                else:
                    params['paramsHelper.%s' % insertedkey] = str(s)
                    logger.debug("Direct inserted %s = %s" % (insertedkey, str(s)))
            else:
                if _ == "query":
                    params['paramsHelper.%s' % insertedkey] = ""
                    logger.debug("Inserted blank %s = ''" % (insertedkey))

        params.update({
            'export': 'true',
            'exportHelper.exportFormat': 'JSON',
            'exportHelper.exportToken': token,
            'paramsHelper.clientNowMillis': token,
            'downloadToken': token,
        })

        if extraparams:
            params.update(extraparams)

        if altstart and altend:
            logger.debug("Applied altstart {0} and altend {1}".format(altstart, altend))
            params['paramsHelper.startTimeMillis'] = altstart
            params['paramsHelper.endTimeMillis'] = altend
            params['paramsHelper.dateFilterPreset'] = 'CUSTOM'

        return params

    @property
    def start(self):
        return int(self.getExportChartHelper()['paramsHelper.startTimeMillis'])

    @property
    def end(self):
        return int(self.getExportChartHelper()['paramsHelper.endTimeMillis'])

    @property
    def messagesurl(self):
        query = urlencode(self.getChartParamsHelper(extraparams={
            'search': 'true',
            'paramsHelper.clientNowMillis': str(self.currentTimeMillis())
        }))
        return '/messages?' + query

    @property
    def chartingurl(self):
        query = urlencode(self.getChartParamsHelper(extraparams={
            'generateMainChart': 'true',
            'paramsHelper.clientNowMillis': str(self.currentTimeMillis())
        }))
        return '/logcharting?' + query

    @once
    def messagesurl_export(self, altstart=None, altend=None, outputformat=None):
        query = urlencode(self.getExportEventsHelper(altstart=altstart, altend=altend, outputformat=outputformat))
        return '/messages?' + query

    @once
    def chartingurl_export(self, altstart=None, altend=None):
        query = urlencode(self.getExportChartHelper(altstart=altstart, altend=altend))
        return '/logcharting?' + query

    @property
    def groupbyfields(self):
        params = self.getExportChartHelper()
        for p in params:
            if p.startswith('paramsHelper.groupByFields'):
                yield p
