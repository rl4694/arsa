import pytest
from unittest.mock import patch
from server.env import get_env

@patch.dict('os.environ', {'test_key': 'test_value'})
def test_get_env_returns_value():
    value = get_env('test_key')
    assert value == 'test_value'

@patch.dict("os.environ", {}, clear=True)
def test_get_env_returns_default():
    value = get_env('missing_key', 'fallback')
    assert value == 'fallback'