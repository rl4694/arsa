# server/tests/test_states.py

import pytest
import server.controllers.states as states
import server.common as common


class TestCreate:
    def test_valid(self):
        old_length = states.length()
        _id = states.create({states.NAME: 'test1'})
        assert common.is_valid_id(_id)
        assert states.length() > old_length
        states.delete(_id)

    def test_non_dict(self):
        with pytest.raises(ValueError):
            states.create(10)

    def test_missing_name(self):
        with pytest.raises(ValueError):
            states.create({})
