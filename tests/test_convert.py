# -*- coding: utf-8 -*-

from __future__ import division

import pytest
import logging
import json
import os

from loginsightexport.convert import convert_to_cfapi, convert_message_to_cfapi, serialize_chunked_json, MAXIMUM_BYTES_POST_BODY
from loginsightexport.convert import arguments, execute


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
logger.setLevel(logging.DEBUG)


@pytest.fixture
def output_file_json():
    JSON = """{"from":1,"to":1,"hasMoreResults":false,"messages":[{"msgId":0,"bucketId":"d747e641-15f6-4e50-a66a-247c029fd038","segOffset":20,"eventType":"v4_957c3660","text":"first message 1","timestamp":1485910595153,"relatedUrls":[],"fields":[{"internalName":"__li_source_path","displayNamespace":null,"displayName":"source","value":"10.16.254.56","fieldType":"STRING","isExtracted":false,"isMeta":true},{"internalName":"event_type","displayNamespace":null,"displayName":"event_type","value":"v4_957c3660","fieldType":"EVENT_TYPE","isExtracted":false,"isMeta":true},{"internalName":"hostname","displayNamespace":null,"displayName":"hostname","value":"10.16.254.56","fieldType":"STRING","isExtracted":false,"isMeta":true}]}],"facetingFields":[{"internalName":"event_type","displayName":"event_type","displayNamespace":null,"fieldType":"EVENT_TYPE","isExtracted":false},{"internalName":"hostname","displayName":"hostname","displayNamespace":null,"fieldType":"STRING","isExtracted":false},{"internalName":"__li_source_path","displayName":"source","displayNamespace":null,"fieldType":"STRING","isExtracted":false}]}"""
    yield json.loads(JSON)


@pytest.fixture
def example_message(output_file_json):
    yield output_file_json['messages'][0]


def test_file_is_json(output_file_json):
    assert isinstance(output_file_json, dict)


def test_file_has_messages(output_file_json):
    assert 'messages' in output_file_json


def test_convert_to_dict(output_file_json, tmpdir):
    assert 'messages' in output_file_json

    d = convert_to_cfapi(output_file_json)

    assert 'events' in d
    for message in d['events']:
        assert 'fields' in message
        assert 'text' in message
        assert 'timestamp' in message

        assert isinstance(message['timestamp'], int)
        assert isinstance(message['text'], str)
        assert isinstance(message['fields'], list)

        for field in message['fields']:
            assert 'name' in field
            assert 'content' in field


def test_serialize_to_json_chunks(output_file_json):
    d = convert_to_cfapi(output_file_json)

    assert len(d['events']) == 1

    chunks = list(serialize_chunked_json(d['events']))
    assert len(chunks) == 1

    for chunk in chunks:
        # Each chunk is stringified JSON containing <=500 events and <=4MB
        assert len(chunk) < MAXIMUM_BYTES_POST_BODY


def test_message_conversion(example_message):
    expected_keys = ['msgId', 'bucketId', 'segOffset', 'eventType', 'text', 'timestamp', 'relatedUrls', 'fields']

    message = convert_message_to_cfapi(example_message)

    assert 'fields' in message
    assert 'text' in message
    assert 'timestamp' in message

    assert isinstance(message['timestamp'], int)
    assert isinstance(message['text'], str)
    assert isinstance(message['fields'], list)

    for field in message['fields']:
        assert 'name' in field
        assert 'content' in field


def test_message_chunking_shortest_results():
    # Empty inputs result in no outputs
    emitted = list(serialize_chunked_json([], max_bytes=9999, max_quantity=9999))
    assert len(emitted) == 0

    # Smallest possible non-empty input results in smallest possible output
    emitted = list(serialize_chunked_json([1], max_bytes=14, max_quantity=9999))
    assert len(emitted) == 1
    assert emitted[0] == '{"events":[1]}'
    assert len(emitted[0]) == 14


def test_message_chunking_by_bytes_limit():
    events = [
        {"a": "1"},
        {"b": "2"},
        {"c": "3"},
    ]

    emitted = list(serialize_chunked_json(events, max_bytes=34, max_quantity=9999))
    assert len(emitted) == 3
    assert emitted[0] == '{"events":[{"a": "1"}]}'
    assert emitted[1] == '{"events":[{"b": "2"}]}'
    assert emitted[2] == '{"events":[{"c": "3"}]}'

    emitted = list(serialize_chunked_json(events, max_bytes=35, max_quantity=9999))
    assert len(emitted) == 2
    assert emitted[0] == '{"events":[{"a": "1"},{"b": "2"}]}'
    assert emitted[1] == '{"events":[{"c": "3"}]}'

    emitted = list(serialize_chunked_json(events, max_bytes=9999, max_quantity=9999))
    assert len(emitted) == 1
    assert emitted[0] == '{"events":[{"a": "1"},{"b": "2"},{"c": "3"}]}'


def test_message_chunking_by_list_limit():
    events = [
        {"a": "1"},
        {"b": "2"},
        {"c": "3"},
    ]

    emitted = list(serialize_chunked_json(events, max_bytes=9999, max_quantity=1))
    assert len(emitted) == 3
    assert emitted[0] == '{"events":[{"a": "1"}]}'
    assert emitted[1] == '{"events":[{"b": "2"}]}'
    assert emitted[2] == '{"events":[{"c": "3"}]}'

    emitted = list(serialize_chunked_json(events, max_bytes=9999, max_quantity=2))
    assert len(emitted) == 2
    assert emitted[0] == '{"events":[{"a": "1"},{"b": "2"}]}'
    assert emitted[1] == '{"events":[{"c": "3"}]}'

    emitted = list(serialize_chunked_json(events, max_bytes=9999, max_quantity=3))
    assert len(emitted) == 1
    assert emitted[0] == '{"events":[{"a": "1"},{"b": "2"},{"c": "3"}]}'


def test_message_chunking_too_small_exceptions():
    events = [
        {"a": "1"},
        {"b": "2"},
        {"c": "3"},
    ]

    with pytest.raises(ValueError) as e:
        list(serialize_chunked_json(events, max_bytes=9999, max_quantity=0))
    assert "max_quantity must be > 0" in str(e)

    with pytest.raises(ValueError) as e:
        list(serialize_chunked_json(events, max_bytes=3, max_quantity=1))
    assert "max_bytes must be > 13" in str(e)

    with pytest.raises(OverflowError) as e:
        list(serialize_chunked_json(events, max_bytes=14, max_quantity=1, raise_on_drop=True))


def test_cli(output_file_json, tmpdir):
    # Create an input file for the converter CLI to operate against
    input_file = os.path.join(str(tmpdir), "input")
    with open(input_file, 'w') as f:
        json.dump(output_file_json, f)

    # Run command
    parser, args = arguments(["-o", str(tmpdir), input_file])
    execute(args)

    # Verify results -- a single new input file was created
    quantity_output_files = 0

    for observed_file in os.listdir(str(tmpdir)):
        if observed_file == "input":
            continue

        assert "input" in observed_file
        quantity_output_files += 1

        fullpath = os.path.join(str(tmpdir), observed_file)

        assert os.path.getsize(fullpath) <= MAXIMUM_BYTES_POST_BODY  # Smaller than limit

        with open(fullpath) as f:
            d = json.load(f)  # Valid JSON
            assert "events" in d

    assert quantity_output_files == 1


def test_cli_usage(capsys):
    with pytest.raises(SystemExit):
        parser, args = arguments([])
    captured = capsys.readouterr()
    assert "arguments are required" in captured[1]


def test_cli_help(capsys):
    with pytest.raises(SystemExit):
        parser, args = arguments(["-h"])

    captured = capsys.readouterr()
    assert "curl" in captured[0]
