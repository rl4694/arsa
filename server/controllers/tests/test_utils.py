import pytest
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
