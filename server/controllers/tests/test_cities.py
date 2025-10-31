import pytest
import server.controllers.cities as ct


@pytest.fixture(autouse=True)
def _reset_store():
    # Reinitialize the module-level dict so tests don't leak state
    if hasattr(ct, "cities") and isinstance(ct.cities, dict):
        ct.cities.clear()
    yield
    if hasattr(ct, "cities") and isinstance(ct.cities, dict):
        ct.cities.clear()


class TestIsValidId:
    def test_valid(self):
        assert ct.is_valid_id('1') == True

    def test_non_str(self):
        assert ct.is_valid_id(1) == False

    def test_empty_str(self):
        assert ct.is_valid_id('') == False


class TestLength():
    @pytest.mark.skip(reason="Length test has been combined into TestCreate")
    def test_basic(self):
        old_length = ct.length()
        _id = ct.create({ct.NAME: 'New York'})
        assert ct.length() > old_length


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
