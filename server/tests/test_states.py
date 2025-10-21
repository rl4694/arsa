# server/tests/test_states.py

import pytest
import server.states as states


class TestIsValidId:
    def test_valid(self):
        assert states.is_valid_id('1') == True

    def test_non_str(self):
        assert states.is_valid_id(1) == False

    def test_empty_str(self):
        assert states.is_valid_id('') == False


class TestCreate:
    def test_valid(self):
        old_length = states.length()
        _id = states.create({states.NAME: 'NY'})
        assert states.is_valid_id(_id)
        assert states.length() > old_length

    def test_non_dict(self):
        with pytest.raises(ValueError):
            states.create(10)

    def test_missing_name(self):
        with pytest.raises(ValueError):
            states.create({})
            
class TestRecursiveCreate:
    def test_state_create_nation(self):
        from server import nations
        state_id = states.create({
            states.NAME: "Test State",
            states.NATION: "Test Nation"
        })
        state_obj = states.read().get(state_id)
        assert state_obj is not None
        
        nation_id = state_obj[states.NATION]
        assert nation_id is not None

        nation = nations.read().get(state_obj[states.NATION])
        assert nation is not None
        assert nation[nations.NAME] == "Test Nation"

