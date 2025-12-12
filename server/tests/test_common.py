import pytest
from server.controllers.crud import is_valid_id

class TestIsValidId:
    def test_basic(self):
        is_valid = is_valid_id('64c13ab08edf48a008793cac')
        assert is_valid == True
    
    def test_invalid_id(self):
        is_valid = is_valid_id('invalid')
        assert is_valid == False
