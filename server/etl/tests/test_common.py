import pytest
import time
import json
from io import StringIO
from unittest.mock import patch, MagicMock, call
import server.etl.common as common
import data.db_connect as dbc
from functools import wraps


class TestIsJsonPopulated:
    def test_populated_dict(self, tmp_path):
        """Test that non-empty dict returns True"""
        filename = tmp_path / "test_data.json"
        with open(filename, 'w') as f:
            json.dump({"key": "value"}, f)
        
        assert common.is_json_populated(str(filename)) is True

    def test_empty_dict(self, tmp_path):
        """Test that empty dict returns False"""
        filename = tmp_path / "test_data.json"
        with open(filename, 'w') as f:
            json.dump({}, f)
        
        assert common.is_json_populated(str(filename)) is False

    def test_populated_list(self, tmp_path):
        """Test that non-empty list returns True"""
        filename = tmp_path / "test_data.json"
        with open(filename, 'w') as f:
            json.dump([1, 2, 3], f)
        
        assert common.is_json_populated(str(filename)) is True

    def test_empty_list(self, tmp_path):
        """Test that empty list returns False"""
        filename = tmp_path / "test_data.json"
        with open(filename, 'w') as f:
            json.dump([], f)
        
        assert common.is_json_populated(str(filename)) is False

    def test_nonexistent_file(self, tmp_path):
        """Test that non-existent file returns False"""
        filename = tmp_path / "nonexistent.json"
        assert common.is_json_populated(str(filename)) is False

    def test_invalid_json(self, tmp_path):
        """Test that invalid JSON returns False"""
        filename = tmp_path / "invalid.json"
        with open(filename, 'w') as f:
            f.write("not valid json {")
        
        assert common.is_json_populated(str(filename)) is False

    def test_json_with_other_types(self, tmp_path):
        """Test that JSON with non-dict/list types returns False"""
        filename = tmp_path / "test_data.json"
        with open(filename, 'w') as f:
            json.dump("just a string", f)
        
        assert common.is_json_populated(str(filename)) is False

    def test_json_with_nested_data(self, tmp_path):
        """Test that nested dict with data returns True"""
        filename = tmp_path / "test_data.json"
        data = {
            "nations": {
                "1": {"name": "USA"},
                "2": {"name": "Canada"}
            }
        }
        with open(filename, 'w') as f:
            json.dump(data, f)
        
        assert common.is_json_populated(str(filename)) is True
