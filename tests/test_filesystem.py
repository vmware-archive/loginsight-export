import pytest
import warnings
import requests_mock
import os.path
import json
import pytest
import logging


from loginsightexport.files import ExportBinToFile, InconsistentFile


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

        with open(export.filename, "x") as f:
            f.write("notjson")

        with pytest.raises(InconsistentFile):
            export.valid
        assert "Not valid JSON" in caplog.text

    def test_missing_required_key_to(self, caplog, tmpdir, root_bin):
        export = ExportBinToFile(root_query=None, bin=root_bin, output_directory=str(tmpdir), output_format='JSON', connection=None)

        with open(export.filename, "x") as f:
            json.dump({"hasMoreResults": False}, fp=f)

        with pytest.raises(InconsistentFile):
            export.valid
        assert "Missing required key 'to'" in caplog.text

    def test_missing_required_key_hasMoreResults(self, caplog, tmpdir, root_bin):
        export = ExportBinToFile(root_query=None, bin=root_bin, output_directory=str(tmpdir), output_format='JSON', connection=None)

        with open(export.filename, "x") as f:
            json.dump({"to": root_bin[2]}, fp=f)

        with pytest.raises(InconsistentFile):
            export.valid
        assert "Missing required key 'hasMoreResults'" in caplog.text

    def test_hasMoreResults_True(self, caplog, tmpdir, root_bin):
        export = ExportBinToFile(root_query=None, bin=root_bin, output_directory=str(tmpdir), output_format='JSON', connection=None)

        with open(export.filename, "x") as f:
            json.dump({"hasMoreResults": True, "to": root_bin[2]}, fp=f)

        with pytest.raises(InconsistentFile):
            export.valid
        assert "Contains hasMoreResults=True, should be False" in caplog.text

    def test_mismatched_quantity(self, caplog, tmpdir, root_bin):
        export = ExportBinToFile(root_query=None, bin=root_bin, output_directory=str(tmpdir), output_format='JSON', connection=None)

        with open(export.filename, "x") as f:
            json.dump({"hasMoreResults": True, "to": 0-root_bin[2]}, fp=f)

        with pytest.raises(InconsistentFile):
            export.valid
        assert "Incorrect quantity of events, found" in caplog.text
