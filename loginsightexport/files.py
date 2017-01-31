# -*- coding: utf-8 -*-

import json
import logging
import os

from .compat import FileNotFoundError

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


class InconsistentFile(OSError):
    """A file whose size is not consistent with expectations, or which is not parsable."""
    def __bool__(self):
        return False

    def __str__(self):
        return "{0} {s.filename!r}: {s.strerror}".format(self.__class__.__name__, s=self)


class ExportBinToFile(object):
    def __init__(self, root_query, bin, output_directory, output_format, connection):
        self.root_query = root_query
        self.bin = bin
        self.filename = os.path.join(output_directory, "output.%s" % bin[0])
        self.logger = logging.getLogger(self.__class__.__name__).getChild("time[{b[0]}-{b[1]}].events[{b[2]}].file[{filename!r}]".format(b=bin, filename=self.filename))
        self.connection = connection
        self.output_format = output_format

    @property
    def valid(self):
        try:
            with open(self.filename, 'r') as f:
                if self.output_format == 'JSON':
                    try:
                        self.body = json.load(f)
                    except ValueError:
                        raise InconsistentFile(0, "Not valid JSON; size {0}".format(os.path.getsize(self.filename)), self.filename)
                    try:
                        if self.bin[2] != self.body['to']:
                            raise InconsistentFile(0, "Incorrect quantity of events, found {body[to]}".format(body=self.body), self.filename)
                        if self.body['hasMoreResults']:
                            raise InconsistentFile(0, "Contains hasMoreResults=True, should be False".format(self.bin), self.filename)
                    except KeyError as e:
                        raise InconsistentFile(0, "Missing required key {0} (possible bug Ref: 1583205)".format(e), self.filename)
                elif self.output_format == 'RAW':
                    pass
                    # TODO: Find a reasonable way to check file validity. Note that multi-line messages are present.
                    found_quantity = sum(1 for line in open(self.filename, 'rb'))
                    if self.bin[2] > found_quantity:
                        raise InconsistentFile(0, "Incorrect quantity of events, should be {b[2]}".format(self.bin), self.filename)
                else:
                    raise ValueError("Unknown output format {0}".format(self.output_format))
            return True
        except InconsistentFile as e:
            self.logger.info(e)
            raise
        except FileNotFoundError:
            raise
        return True

    def download(self):
        export_chunk_url = self.root_query.messagesurl_export(altstart=self.bin[0], altend=self.bin[1], outputformat=self.output_format)

        with open(self.filename, 'xb') as f:  # write-exclusive binary -- fails if the file already exists
            bytes = 0
            r = self.connection.get(export_chunk_url, stream=True)
            for chunk in r.iter_content(chunk_size=512):  # 1024 * 1024 = 10MB chunk size
                bytes += len(chunk)
                f.write(chunk)
        return bytes
