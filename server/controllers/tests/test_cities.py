import pytest
import server.controllers.cities as ct
import data.db_connect as dbc
import mongomock


@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    def fake_connect():
        client = mongomock.MongoClient()
        return client['testDB']
    monkeypatch.setattr(dbc, "connect_db", fake_connect)


class TestIsValidId:
    def test_valid(self):
        assert ct.is_valid_id('507f1f77bcf86cd799439011') == True

    def test_non_str(self):
        assert ct.is_valid_id(1) == False

    def test_empty_str(self):
        assert ct.is_valid_id('') == False


class TestLength():
    def test_basic(self):
        assert ct.length() == 0
        id1 = ct.create({ct.NAME: "alpha"})
        id2 = ct.create({ct.NAME: "bravo"})
        assert ct.length() == 2
        ct.delete(id1)
        assert ct.length() == 1
        ct.delete(id2)
        assert ct.length() == 0


class TestCreate:
    def test_valid(self):
        _id = ct.create({ct.NAME: 'testcity'})
        assert ct.is_valid_id(_id)
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
