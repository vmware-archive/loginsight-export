# -*- coding: utf-8 -*-

import logging
import sys
import collections
import datetime
import humanize

from .compat import current_time


# Copyright © 2017 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the “License”); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an “AS IS” BASIS, without warranties or
# conditions of any kind, EITHER EXPRESS OR IMPLIED. See the License for the
# specific language governing permissions and limitations under the License.


class ProgressRange(collections.Iterator):
    logger = logging.getLogger(__name__)

    def __init__(self, bins=[(0, 0, 0)], prelude="Planning", suffix="requests", columns=100):
        self.columns = columns
        self.prelude = prelude
        self.suffix = suffix
        self.updates = 0
        self.start(bins)
        self.longest_line = 0
        self.started_at = current_time()
        self.duration = 0

    def start(self, bins):
        self._start = min([x[0] for x in bins])
        self._end = max([x[1] for x in bins])
        self.totalrange = self._end - self._start

    def __enter__(self):
        return self

    def update(self, bins, increment=1):
        self.duration = datetime.timedelta(seconds=current_time() - self.started_at)
        self.updates += increment
        start = min([x[0] for x in bins])
        endin = max([x[1] for x in bins])
        percent_start = ((start - self._start) / float(self.totalrange))
        percent_endin = ((endin - self._start) / float(self.totalrange))

        filledStart = int(round(self.columns * percent_start))
        filledEndin = int(round(self.columns * percent_endin))
        percent = sum([filledStart, filledEndin]) / 2

        if not self.logger.isEnabledFor(logging.WARNING):
            return
        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info("{s.prelude} consider time range {start}-{endin} = {percent:.1f}% {s.updates} {s.suffix} ({s.duration} elapsed)".format(s=self, start=start, endin=endin, bin=bin, percent=percent))
            return

        if filledStart == filledEndin:
            filledEndin = max(self.columns, filledEndin + 1)  # clamp

        bar = '-' * filledStart + '=' * (filledEndin - filledStart) + '-' * (self.columns - filledEndin)
        out = "\r{s.prelude} [{bar}] {percent:.1f}% {s.updates} {s.suffix} ({duration} elapsed)".format(bar=bar, s=self, percent=percent, duration=humanize.naturaldelta(self.duration))

        self.longest_line = max(self.longest_line, len(out))
        sys.stdout.write(out)
        sys.stdout.write(" " * (len(out) - self.longest_line))  # white out over remaining characters from previous line
        sys.stdout.flush()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.prelude = "Aborted "
        else:
            self.update([(self._end, self._end, 0)], increment=0)  # TODO: BUG: This results in a progress bar at 50% full of ====

        if not self.logger.isEnabledFor(logging.WARNING) or self.logger.isEnabledFor(logging.INFO):
            return
        sys.stdout.write("\n")  # write and flush a newline at the end of the progress bar
        sys.stdout.flush()
        return


class ProgressBar(collections.Iterator):
    def __init__(self, iterable, start=0, prelude="Download", suffix="", columns=100, quiet=False, log=False, extra=None):
        self.current = start
        self.total = len(iterable)
        self.columns = columns
        self.prelude = prelude
        self.suffix = suffix
        self.longest_line = 0
        self._iterator = iter(iterable)
        self.quiet = quiet
        self.log = log
        self.stats = collections.Counter()
        self.started_at = current_time()
        self.duration = 0

    def __enter__(self):
        return self

    def __iter__(self):
        return self

    def __next__(self):
        _ = next(self._iterator)
        self.update(1)
        return _

    next = __next__

    def update(self, increment=1):
        self.duration = datetime.timedelta(seconds=current_time() - self.started_at)
        self.current += increment
        try:
            percent = 100 * (self.current / float(self.total))
            filled_length = int(round(self.columns * self.current / float(self.total)))
        except ZeroDivisionError:
            percent = 0
            filled_length = 0

        if self.quiet:
            return
        if self.log:
            logger = logging.getLogger(__name__)
            logger.info("{s.prelude} {percent:.1f}% = {s.current}/{s.total} {s.suffix} ({s.duration} elapsed)".format(s=self, percent=percent))
            return

        bar = '=' * filled_length + '-' * (self.columns - filled_length)
        out = "\r{s.prelude} [{bar}] {percent:.1f}% {s.current}/{s.total} {s.suffix} ({duration} elapsed)".format(bar=bar, s=self, percent=percent, duration=humanize.naturaldelta(self.duration))
        self.longest_line = max(self.longest_line, len(out))
        sys.stdout.write(out)
        sys.stdout.flush()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.current = self.total
        else:
            self.prelude = "Aborted "
        self.update(0)
        if not (self.quiet or self.log):
            sys.stdout.write("\n")  # write and flush a newline at the end of the progress bar
            sys.stdout.flush()
