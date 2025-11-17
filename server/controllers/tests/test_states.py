# server/tests/test_states.py
import pytest
import server.controllers.states as st
import server.common as common
import data.db_connect as dbc

SAMPLE_NAME = "test_state"
SAMPLE_NATION = "test_nation"
SAMPLE_KEY = SAMPLE_NAME
SAMPLE_STATE = {
    st.NAME: SAMPLE_NAME,
    st.NATION: SAMPLE_NATION,
}


class TestLength:
    def test_basic(self):
        old_length = st.length()
        _id = st.create(SAMPLE_STATE)
        assert st.length() == old_length + 1
        st.delete(_id)
        assert st.length() == old_length


class TestCreate:
    def test_valid(self):
        _id = st.create(SAMPLE_STATE)
        assert common.is_valid_id(_id)
        states = st.read()
        assert SAMPLE_KEY in states
        st.delete(_id)

    def test_non_dict(self):
        with pytest.raises(ValueError):
            st.create(10)

    def test_missing_name(self):
        with pytest.raises(ValueError):
            st.create({})


class TestRead:
    def test_basic(self):
        _id = st.create(SAMPLE_STATE)
        states = st.read()
        assert isinstance(states, dict)
        assert SAMPLE_KEY in states
        assert len(states) > 0
        st.delete(_id)


class TestUpdate:
    def test_basic(self):
        _id = st.create(SAMPLE_STATE)
        new_nation = 'new_nation'
        st.update(_id, {st.NAME: SAMPLE_NAME, st.NATION: new_nation})
        states = st.read()
        assert SAMPLE_KEY in states
        assert states[SAMPLE_KEY][st.NATION] == new_nation
        st.delete(_id)


class TestDelete:
    def test_basic(self):
        _id = st.create(SAMPLE_STATE)
        st.delete(_id)
        states = st.read()
        assert SAMPLE_KEY not in states
