import pytest
import server.controllers.cities as ct
import server.common as common

SAMPLE_NAME = 'test_city'
SAMPLE_STATE = 'test_state'
SAMPLE_NATION = 'test_nation'
SAMPLE_KEY = (SAMPLE_NAME, SAMPLE_STATE)
SAMPLE_CITY = {
    ct.NAME: SAMPLE_NAME,
    ct.STATE: SAMPLE_STATE,
    ct.NATION: SAMPLE_NATION,
}


class TestLength():
    def test_basic(self):
        old_length = ct.length()
        _id = ct.create(SAMPLE_CITY)
        assert ct.length() == old_length + 1
        ct.delete(SAMPLE_KEY)
        assert ct.length() == old_length


class TestCreate:
    def test_valid(self):
        _id = ct.create(SAMPLE_CITY)
        assert common.is_valid_id(_id)
        cities = ct.read()
        assert SAMPLE_KEY in cities
        ct.delete(SAMPLE_KEY)

    def test_non_dict(self):
        with pytest.raises(ValueError):
            ct.create(10)

    def test_missing_name(self):
        with pytest.raises(ValueError):
            ct.create({})


class TestRead:
    def test_basic(self):
        _id = ct.create(SAMPLE_CITY)
        cities = ct.read()
        assert isinstance(cities, dict)
        assert SAMPLE_KEY in cities
        assert len(cities) > 0
        ct.delete(SAMPLE_KEY)


class TestUpdate:
    def test_basic(self):
        _id = ct.create(SAMPLE_CITY)
        new_state = 'new_state'
        new_key = (SAMPLE_NAME, new_state)
        ct.update(SAMPLE_KEY, {ct.STATE: new_state})
        cities = ct.read()
        new_city = cities[new_key]
        
        assert new_key in cities
        assert new_city[ct.NAME] == SAMPLE_NAME
        assert new_city[ct.STATE] == new_state
        assert new_city[ct.NATION] == SAMPLE_NATION
        ct.delete(new_key)

    def test_non_dict(self):
        with pytest.raises(ValueError):
            ct.update(SAMPLE_KEY, 123)

    def test_invalid_key(self):
        with pytest.raises(ValueError):
            ct.update((SAMPLE_NAME), 123)


class TestDelete:
    def test_basic(self):
        _id = ct.create(SAMPLE_CITY)
        ct.delete(SAMPLE_KEY)
        cities = ct.read()
        assert SAMPLE_KEY not in cities

    def test_invalid_key(self):
        with pytest.raises(ValueError):
            ct.update((SAMPLE_NAME), 123)
