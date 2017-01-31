# -*- coding: utf-8 -*-

import os.path
import json
import pytest

from loginsightexport.files import ExportBinToFile, InconsistentFile, FileNotFoundError


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


@pytest.fixture()
def root_bin():
    return 1, 4, 55


class TestExistingFileValidity(object):

    def test_missing_file(self, caplog, tmpdir, root_bin):
        export = ExportBinToFile(root_query=None, bin=root_bin, output_directory=str(tmpdir), output_format='JSON', connection=None)

        assert not os.path.exists(export.filename)

        with pytest.raises(FileNotFoundError):
            export.valid
        assert len(caplog.records) == 0

    def test_not_json_file(self, caplog, tmpdir, root_bin):
        export = ExportBinToFile(root_query=None, bin=root_bin, output_directory=str(tmpdir), output_format='JSON', connection=None)

        with open(export.filename, "w") as f:
            f.write("notjson")

        with pytest.raises(InconsistentFile):
            export.valid
        assert "Not valid JSON" in caplog.text

    def test_missing_required_key_to(self, caplog, tmpdir, root_bin):
        export = ExportBinToFile(root_query=None, bin=root_bin, output_directory=str(tmpdir), output_format='JSON', connection=None)

        with open(export.filename, "w") as f:
            json.dump({"hasMoreResults": False}, fp=f)

        with pytest.raises(InconsistentFile):
            export.valid
        assert "Missing required key 'to'" in caplog.text

    def test_missing_required_key_hasMoreResults(self, caplog, tmpdir, root_bin):
        export = ExportBinToFile(root_query=None, bin=root_bin, output_directory=str(tmpdir), output_format='JSON', connection=None)

        with open(export.filename, "w") as f:
            json.dump({"to": root_bin[2]}, fp=f)

        with pytest.raises(InconsistentFile):
            export.valid
        assert "Missing required key 'hasMoreResults'" in caplog.text

    def test_hasMoreResults_True(self, caplog, tmpdir, root_bin):
        export = ExportBinToFile(root_query=None, bin=root_bin, output_directory=str(tmpdir), output_format='JSON', connection=None)

        with open(export.filename, "w") as f:
            json.dump({"hasMoreResults": True, "to": root_bin[2]}, fp=f)

        with pytest.raises(InconsistentFile):
            export.valid
        assert "Contains hasMoreResults=True, should be False" in caplog.text

    def test_mismatched_quantity(self, caplog, tmpdir, root_bin):
        export = ExportBinToFile(root_query=None, bin=root_bin, output_directory=str(tmpdir), output_format='JSON', connection=None)

        with open(export.filename, "w") as f:
            json.dump({"hasMoreResults": True, "to": 0 - root_bin[2]}, fp=f)

        with pytest.raises(InconsistentFile):
            export.valid
        assert "Incorrect quantity of events, found" in caplog.text
