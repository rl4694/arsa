# server/tests/test_states.py
import pytest
import server.controllers.states as st
import server.common as common

SAMPLE_NAME = 'test_state'
SAMPLE_NATION = 'test_nation'
SAMPLE_KEY = (SAMPLE_NAME, SAMPLE_NATION)
SAMPLE_STATE = {
    st.NAME: SAMPLE_NAME,
    st.NATION: SAMPLE_NATION,
}


class TestLength:
    def test_basic(self):
        old_length = st.length()
        _id = st.create(SAMPLE_STATE)
        assert st.length() == old_length + 1
        st.delete(SAMPLE_KEY)
        assert st.length() == old_length


class TestCreate:
    def test_valid(self):
        _id = st.create(SAMPLE_STATE)
        assert common.is_valid_id(_id)
        states = st.read()
        assert SAMPLE_KEY in states
        st.delete(SAMPLE_KEY)

    def test_non_dict(self):
        with pytest.raises(ValueError):
            st.create(10)

    def test_missing_name(self):
        with pytest.raises(ValueError):
            st.create({st.NATION: SAMPLE_NATION})

    def test_missing_nation(self):
        with pytest.raises(ValueError):
            st.create({st.NAME: SAMPLE_NAME})


class TestRead:
    def test_basic(self):
        _id = st.create(SAMPLE_STATE)
        states = st.read()
        assert isinstance(states, dict)
        assert SAMPLE_KEY in states
        assert len(states) > 0
        st.delete(SAMPLE_KEY)


class TestUpdate:
    def test_basic(self):
        _id = st.create(SAMPLE_STATE)
        new_nation = 'new_nation'
        new_key = (SAMPLE_NAME, new_nation)
        st.update(SAMPLE_KEY, {st.NATION: new_nation})
        states = st.read()
        new_state = states[new_key]

        assert new_key in states
        assert new_state[st.NAME] == SAMPLE_NAME
        assert new_state[st.NATION] == new_nation
        st.delete(new_key)

    def test_non_dict(self):
        with pytest.raises(ValueError):
            st.update(SAMPLE_KEY, 123)

    def test_invalid_key(self):
        with pytest.raises(ValueError):
            st.update((SAMPLE_NAME), 123)


class TestDelete:
    def test_basic(self):
        _id = st.create(SAMPLE_STATE)
        st.delete(SAMPLE_KEY)
        states = st.read()
        assert SAMPLE_KEY not in states

    def test_invalid_key(self):
        with pytest.raises(ValueError):
            st.update((SAMPLE_NAME), 123)
