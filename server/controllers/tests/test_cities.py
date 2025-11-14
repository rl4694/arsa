import pytest
import server.controllers.cities as ct
import server.common as common
import data.db_connect as dbc

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
        ct.delete(_id)
        assert ct.length() == old_length


class TestCreate:
    def test_valid(self):
        _id = ct.create(SAMPLE_CITY)
        assert common.is_valid_id(_id)
        cities = ct.read()
        assert SAMPLE_KEY in cities
        ct.delete(_id)

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
        ct.delete(_id)


class TestUpdate:
    def test_basic(self):
        _id = ct.create(SAMPLE_CITY)
        new_state = 'new_state'
        new_key = (SAMPLE_NAME, new_state)
        ct.update(_id, {ct.NAME: SAMPLE_NAME, ct.STATE: new_state})
        cities = ct.read()
        
        assert new_key in cities
        assert cities[new_key][ct.STATE] == new_state
        ct.delete(_id)


class TestDelete:
    def test_basic(self):
        _id = ct.create(SAMPLE_CITY)
        ct.delete(_id)
        cities = ct.read()
        assert SAMPLE_KEY not in cities
