import pytest
import server.cities as ct


class TestIsValidId:
    def test_valid(self):
        assert ct.is_valid_id('1') == True

    def test_non_str(self):
        assert ct.is_valid_id(1) == False

    def test_empty_str(self):
        assert ct.is_valid_id('') == False


class TestCreate:
    def test_valid(self):
        old_length = ct.length()
        _id = ct.create({ct.NAME: 'New York'})
        assert ct.is_valid_id(_id)
        assert ct.length() > old_length

    def test_non_dict(self):
        with pytest.raises(ValueError):
            ct.create(10)

    def test_missing_name(self):
        with pytest.raises(ValueError):
            ct.create({})


class TestRead:
    def test_basic(self):
        ct.create({ct.NAME: 'New York'})
        cities = ct.read()
        assert isinstance(cities, dict)
        assert len(cities) > 0
        
class TestRecursiveCreate:
    def test_city_create_state(self):
        from server import states, nations
        city_id = ct.create({
            ct.NAME: "Test City",
            ct.STATE: "Test State",
            ct.NATION: "Test Nation"
        })
        city = ct.read().get(city_id)
        assert city is not None

        state_id = city[ct.STATE]
        assert state_id is not None

        state = states.read().get(city[ct.STATE])
        assert state is not None
        assert state[states.NAME] == "Test State"
        nation_id = state[states.NATION]
        assert nation_id is not None

        nation = nations.read().get(nation_id)
        assert nation is not None
        assert nation[nations.NAME] == "Test Nation"
        
        assert city[ct.NATION] == nation_id
