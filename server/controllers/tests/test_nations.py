import pytest
import server.controllers.nations as nt
import server.common as common


@pytest.fixture(autouse=True)
def _reset_store():
    # Reinitialize the module-level dict so tests don't leak state
    if hasattr(nt, "nations") and isinstance(nt.nations, dict):
        nt.nations.clear()
    yield
    if hasattr(nt, "nations") and isinstance(nt.nations, dict):
        nt.nations.clear()


class TestCreate:
    def test_valid(self):
        old_length = nt.length()
        _id = nt.create({nt.NAME: "test1"})
        assert common.is_valid_id(_id)
        assert nt.length() > old_length
        nt.delete(_id)

    def test_non_dict(self):
        with pytest.raises(ValueError):
            nt.create(10)

    def test_missing_name(self):
        with pytest.raises(ValueError):
            nt.create({})


class TestRead:
    def test_basic(self):
        _id = nt.create({nt.NAME: "test1"})
        nations = nt.read()
        assert isinstance(nations, dict)
        assert len(nations) > 0
        nt.delete(_id)
