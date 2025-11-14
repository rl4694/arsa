import pytest
import server.controllers.cities as ct
import server.common as common
import data.db_connect as dbc


class TestLength():
    def test_basic(self):
        old_length = ct.length()
        id1 = ct.create({ct.NAME: "alpha"})
        id2 = ct.create({ct.NAME: "bravo"})
        assert ct.length() == old_length + 2
        ct.delete(id1)
        assert ct.length() == old_length + 1
        ct.delete(id2)
        assert ct.length() == old_length


class TestCreate:
    def test_valid(self):
        _id = ct.create({ct.NAME: 'testcity'})
        assert common.is_valid_id(_id)
        cities = ct.read()
        assert _id in cities
        ct.delete(_id)

    def test_non_dict(self):
        with pytest.raises(ValueError):
            ct.create(10)

    def test_missing_name(self):
        with pytest.raises(ValueError):
            ct.create({})


class TestRead:
    def test_basic(self):
        _id = ct.create({ct.NAME: 'test1'})
        cities = ct.read()
        assert isinstance(cities, dict)
        assert _id in cities
        assert len(cities) > 0
        ct.delete(_id)


class TestUpdate:
    def test_basic(self):
        _id = ct.create({ct.NAME: 'updatecity', ct.STATE: 'old'})
        ct.update(_id, {ct.NAME: 'updatecity', ct.STATE: 'new'})
        cities = ct.read()
        assert cities[_id][ct.STATE] == 'new'
        ct.delete(_id)


class TestDelete:
    def test_basic(self):
        _id = ct.create({ct.NAME: 'delcity'})
        ct.delete(_id)
        cities = ct.read()
        assert _id not in cities
