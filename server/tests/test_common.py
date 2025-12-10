import pytest
import server.common as common

class TestIsValidId:
    def test_basic(self):
        is_valid = common.is_valid_id('64c13ab08edf48a008793cac')
        assert is_valid == True
    
    def test_invalid_id(self):
        is_valid = common.is_valid_id('invalid')
        assert is_valid == False
