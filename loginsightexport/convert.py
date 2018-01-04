# -*- coding: utf-8 -*-

"""
Convert exported JSON-formatted events from a VMware vRealize Log Insight server
to a format suitible for reimporting via the ingestion api directly.
Splits output files to conform to the ingestion api limits (bytes and length),
which may result in a large number of small files.
Does not establish network connections; use curl or similar to reimport.
"""

import logging
import json
import re
import os
import sys

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

MAXIMUM_BYTES_TEXT_FIELD = 1024 * 16  # 16 KB (text field)
MAXIMUM_BYTES_POST_BODY = 1024 * 1024 * 4  # 4 MB per HTTP POST request
MAXIMUM_MESSAGES_BUFFER = 500


def crush_invalid_field_name(name):
    """Given a proposed field name, replace banned characters with underscores, and convert any run of underscores with a single."""
    if name[0].isdigit():
        name = "_%s" % name
    name = re.sub(r'[^a-z0-9_]', "_", name.lower())
    return re.sub(r'__*', "_", name, flags=re.I)


def map_field(field):
    """Given a export-format field dictionary, produce a CFAPI-format field dictionary."""
    return {'name': crush_invalid_field_name(field.get("internalName", field.get("displayName"))), 'content': field.get("value")}


def convert_message_to_cfapi(message, reserved_fields=('event_type',)):
    """Given an export-format message, produce a CFAPI-format message."""
    return {'text': message['text'][:MAXIMUM_BYTES_TEXT_FIELD], 'timestamp': message['timestamp'], 'fields': [map_field(f) for f in message['fields'] if f.get("internalName", None) not in reserved_fields]}


def convert_to_cfapi(input_dict):
    """Given a dict-like object of the JSON export-format, produce a dict serializable to CFAPI-compataible json"""

    if input_dict.get('hasMoreResults', None) is True:
        logger.warning("Input dict marked as having more results")

    return {"events": [convert_message_to_cfapi(m) for m in input_dict['messages']]}


def serialize_chunked_json(lst, prelude='{"events":[', trailer=']}', sep=',', max_bytes=MAXIMUM_BYTES_POST_BODY, max_quantity=MAXIMUM_MESSAGES_BUFFER, raise_on_drop=False):
    """
    Efficiently serialize a list of items into JSON that's limited by both max_bytes post-serialization and max_quantity items.

    :param lst: a list of JSON-serializable objects
    :param prelude: String to prepend to serialized text, canonically start of a hashmap.
    :param trailer: String to append to serialized text, canonically ending the hashmap started by the prelude.
    :param sep: String seperator for joining already-serialized items.
    :return: yields a sequence of stringified json, each containing the prelude and trailer.
    """

    overhead = len(prelude) + len(trailer)
    maximum_payload_size = max_bytes - overhead

    if max_quantity <= 0:
        raise ValueError("max_quantity must be > 0")
    if maximum_payload_size <= 0:
        raise ValueError("max_bytes must be > %d to include prelude+trailer" % overhead)

    result = []
    result_size = 0

    for item in lst:
        serialized = json.dumps(item)
        if result_size + len(sep) + len(serialized) > maximum_payload_size or len(result) >= max_quantity:

            if result_size:
                yield prelude + sep.join(result) + trailer
                result = []
                result_size = 0
            elif raise_on_drop:
                raise OverflowError("Item size %d > maximum %d: %s" % (len(serialized), maximum_payload_size, serialized))
            else:
                logger.warning("Dropping item size %d > maximum %d: %s" % (len(serialized), maximum_payload_size, serialized))

        result.append(serialized)
        result_size += len(sep) + len(serialized)

    if result_size:
        yield prelude + sep.join(result) + trailer


def arguments(commandline=None):
    import shutil
    import argparse

    # Try to discover the window size, so argparse can draw appropriately-wrapped help.
    os.environ['COLUMNS'] = str(min([120, shutil.get_terminal_size().columns]))

    parser = argparse.ArgumentParser(
        description=__doc__,
        usage='%(prog)s -o outputdir/ file1 [file2 ...]',
        epilog="Import Hint: for X in OUTPUTDIR/*; do curl -k -d @$X https://li.example.com:9543/api/v1/events/ingest/0; done"
    )
    parser.add_argument('file', metavar="file", nargs="+", default=[], help="JSON-formatted files produced by `loginsight-export`")
    parser.add_argument('-o', '--output',
                        required=True,
                        metavar="DIR",
                        help="Write converted data to this existing directory.")

    loggroup = parser.add_argument_group("Display")
    loggroup.add_argument("-q", "--quiet", action="store_const", const=1, default=0, help="Silence progressbar.")
    loggroup.add_argument("-v", "--verbose", action="count", default=0, dest="loglevel", help="Replace progressbar with logs. -vv writes PII (urls & queries) to stdout")

    parser.add_argument("--maxlength", type=int, default=MAXIMUM_MESSAGES_BUFFER, help="Largest quantity of messages to write in a single bin, default %(default)s")
    parser.add_argument("--maxbytes", type=int, default=MAXIMUM_BYTES_POST_BODY, help="Largest byte size of messages to write in a single bin, default %(default)s")

    args = parser.parse_args(commandline)

    if not os.path.isdir(args.output):
        parser.error("{0} is not a directory".format(args.output))

    args.loglevel -= args.quiet

    return parser, args


def setup_logger(args):
    # Set up logging according to command-line verbosity
    logger = logging.getLogger()
    logger.setLevel(int(30 - (args.loglevel * 10)))
    ch = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(u'%(asctime)s %(name)s %(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.info("Set logging level to {0}".format(logging.getLevelName(logger.getEffectiveLevel())))
    return logger


def execute(args):
    from tempfile import NamedTemporaryFile

    dots = logger.isEnabledFor(logging.WARNING) and not logger.isEnabledFor(logging.INFO)
    for input_filename in args.file:
        logger.info("Reading input file %s" % input_filename)
        with open(input_filename) as f:
            d = json.load(f)

        for emitting_file_payload in serialize_chunked_json(convert_to_cfapi(d)['events']):
            with NamedTemporaryFile(mode="w", prefix=os.path.basename(input_filename) + "-", dir=args.output, delete=False) as output_file:
                logger.debug("Writing output file %s" % output_file.name)
                output_file.write(emitting_file_payload)
        if dots:
            print(".", end="")

    if dots:
        print()


def main():
    parser, args = arguments()
    setup_logger(args)
    execute(args)


if __name__ == "__main__":
    main()
