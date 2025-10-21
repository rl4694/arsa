import pytest
import server.cities as ct


class TestIsValidId:
    def test_valid(self):
        assert ct.is_valid_id('1') == True

    def test_non_str(self):
        assert ct.is_valid_id(1) == False

    def test_empty_str(self):
        assert ct.is_valid_id('') == False

#test create is outdated
'''
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
'''

class TestRead:
    def test_basic(self):
        ct.create({ct.NAME: 'New York'})
        cities = ct.read()
        assert isinstance(cities, dict)
        assert len(cities) > 0
        
class TestRecursiveCreate:
    def setup_method(self):
        ct.read().clear()
        from server import states, nations
        states.read().clear()
        nations.read().clear()

        self.city_id = ct.create({
            ct.NAME: "Test City",
            ct.STATE: "Test State",
            ct.NATION: "Test Nation"
        })

        self.city = ct.read().get(self.city_id)
        self.state_id = self.city[ct.STATE]
        self.state = states.read().get(self.state_id)
        self.nation_id = self.state["nation"]
        self.nation = nations.read().get(self.nation_id)
    def test_city_exists(self):
        assert self.city is not None
        
    def test_state_created(self):
        assert self.state_id is not None
        assert self.state is not None
        assert self.state["name"] == "Test State"

    def test_nation_created(self):
        assert self.nation_id is not None
        assert self.nation is not None
        assert self.nation["name"] == "Test Nation"

    def test_city_links_correct_nation(self):
        assert self.city["nation"] == self.nation_id
