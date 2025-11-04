import pytest
import json
import server.controllers.utils as utils

class TestJson:
    def test_valid(self, tmp_path):
        filename = tmp_path / "test_data.json"
        data = {
            "key": "value",
            "number": 42,
        }
        utils.save_json(str(filename), data)
        assert filename.exists()
        
        loaded = utils.load_json(str(filename))
        assert loaded == data

    def test_nonexistent_file(self, tmp_path):
        filename = tmp_path / "test_data.json"
        with pytest.raises(FileNotFoundError):
            loaded = utils.load_json(str(filename))
    
    def test_non_dict_save(self, tmp_path):
        filename = tmp_path / "test_data.json"
        with pytest.raises(ValueError):
            utils.save_json(str(filename), 123)


class TestIsJsonPopulated:
    def test_populated_dict(self, tmp_path):
        """Test that non-empty dict returns True"""
        filename = tmp_path / "test_data.json"
        with open(filename, 'w') as f:
            json.dump({"key": "value"}, f)
        
        assert utils.is_json_populated(str(filename)) is True

    def test_empty_dict(self, tmp_path):
        """Test that empty dict returns False"""
        filename = tmp_path / "test_data.json"
        with open(filename, 'w') as f:
            json.dump({}, f)
        
        assert utils.is_json_populated(str(filename)) is False

    def test_populated_list(self, tmp_path):
        """Test that non-empty list returns True"""
        filename = tmp_path / "test_data.json"
        with open(filename, 'w') as f:
            json.dump([1, 2, 3], f)
        
        assert utils.is_json_populated(str(filename)) is True

    def test_empty_list(self, tmp_path):
        """Test that empty list returns False"""
        filename = tmp_path / "test_data.json"
        with open(filename, 'w') as f:
            json.dump([], f)
        
        assert utils.is_json_populated(str(filename)) is False

    def test_nonexistent_file(self, tmp_path):
        """Test that non-existent file returns False"""
        filename = tmp_path / "nonexistent.json"
        assert utils.is_json_populated(str(filename)) is False

    def test_invalid_json(self, tmp_path):
        """Test that invalid JSON returns False"""
        filename = tmp_path / "invalid.json"
        with open(filename, 'w') as f:
            f.write("not valid json {")
        
        assert utils.is_json_populated(str(filename)) is False

    def test_json_with_other_types(self, tmp_path):
        """Test that JSON with non-dict/list types returns False"""
        filename = tmp_path / "test_data.json"
        with open(filename, 'w') as f:
            json.dump("just a string", f)
        
        assert utils.is_json_populated(str(filename)) is False

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
        
        assert utils.is_json_populated(str(filename)) is True
