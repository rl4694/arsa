import pytest
import server.controllers.nations as nt
import server.common as common

SAMPLE_NAME = 'test_nation'
SAMPLE_KEY = SAMPLE_NAME
SAMPLE_NATION = {
    nt.NAME: SAMPLE_NAME,
}


@pytest.fixture(autouse=True)
def _reset_store():
    # Reinitialize the module-level dict so tests don't leak state
    if hasattr(nt, "nations") and isinstance(nt.nations, dict):
        nt.nations.clear()
    yield
    if hasattr(nt, "nations") and isinstance(nt.nations, dict):
        nt.nations.clear()


class TestLength:
    def test_basic(self):
        old_length = nt.length()
        _id = nt.create(SAMPLE_NATION)
        assert nt.length() == old_length + 1
        nt.delete(_id)
        assert nt.length() == old_length


class TestCreate:
    def test_valid(self):
        _id = nt.create(SAMPLE_NATION)
        assert common.is_valid_id(_id)
        nations = nt.read()
        assert SAMPLE_KEY in nations
        nt.delete(_id)

    def test_non_dict(self):
        with pytest.raises(ValueError):
            nt.create(10)

    def test_missing_name(self):
        with pytest.raises(ValueError):
            nt.create({})


class TestRead:
    def test_basic(self):
        _id = nt.create(SAMPLE_NATION)
        nations = nt.read()
        assert isinstance(nations, dict)
        assert SAMPLE_KEY in nations
        assert len(nations) > 0
        nt.delete(_id)


class TestUpdate:
    def test_basic(self):
        _id = nt.create(SAMPLE_NATION)
        new_name = 'new_nation'
        nt.update(_id, {nt.NAME: new_name})
        nations = nt.read()
        assert new_name in nations
        assert nations[new_name][nt.NAME] == new_name
        nt.delete(_id)


class TestDelete:
    def test_basic(self):
        _id = nt.create(SAMPLE_NATION)
        nt.delete(_id)
        nations = nt.read()
        assert SAMPLE_KEY not in nations
