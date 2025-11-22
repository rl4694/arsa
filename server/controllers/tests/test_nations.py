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
        nt.delete(SAMPLE_NAME)
        assert nt.length() == old_length


class TestCreate:
    def test_valid(self):
        _id = nt.create(SAMPLE_NATION)
        assert common.is_valid_id(_id)
        nations = nt.read()
        assert any(doc.get(nt.NAME) == SAMPLE_KEY for doc in nations.values())
        nt.delete(SAMPLE_NAME)

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
        assert any(doc.get(nt.NAME) == SAMPLE_KEY for doc in nations.values())
        assert len(nations) > 0
        nt.delete(SAMPLE_NAME)


class TestUpdate:
    def test_basic(self):
        _id = nt.create(SAMPLE_NATION)
        new_name = 'new_nation'
        nt.update(SAMPLE_NAME, {nt.NAME: new_name})
        nations = nt.read()
        assert any(doc.get(nt.NAME) == new_name for doc in nations.values())
        updated_docs = [doc for doc in nations.values() if doc.get(nt.NAME) == new_name]
        assert updated_docs and updated_docs[0][nt.NAME] == new_name
        nt.delete(new_name)


class TestDelete:
    def test_basic(self):
        _id = nt.create(SAMPLE_NATION)
        nt.delete(SAMPLE_NAME)
        nations = nt.read()
        assert all(doc.get(nt.NAME) != SAMPLE_KEY for doc in nations.values())
