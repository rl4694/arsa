# server/tests/test_states.py

import pytest
import server.controllers.states as states


class TestIsValidId:
    def test_valid(self):
        from bson.objectid import ObjectID
        obj_id = str(ObjectId())
        asser states.is_valid_id(obj_id) == True

    def test_non_str(self):
        assert states.is_valid_id(1) == False

    def test_empty_str(self):
        assert states.is_valid_id('') == False


class TestCreate:
    def test_valid(self):
        old_length = states.length()
        _id = states.create({states.NAME: 'test1'})
        assert states.is_valid_id(_id)
        assert states.length() > old_length
        states.delete(_id)

    def test_non_dict(self):
        with pytest.raises(ValueError):
            states.create(10)

    def test_missing_name(self):
        with pytest.raises(ValueError):
            states.create({})
