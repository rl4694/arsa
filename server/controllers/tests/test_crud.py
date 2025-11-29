# server/tests/test_states.py
import pytest
import server.common as common
from server.controllers.crud import CRUD

FIELD1 = 'field1'
FIELD2 = 'field2'
FIELD3 = 'field3'
SAMPLE_FIELD1 = 'sample1'
SAMPLE_FIELD2 = 'sample2'
SAMPLE_FIELD3 = 'sample3'
SAMPLE_KEY = (SAMPLE_FIELD1, SAMPLE_FIELD2)
SAMPLE_RECORD = {
    FIELD1: SAMPLE_FIELD1,
    FIELD2: SAMPLE_FIELD2,
    FIELD3: SAMPLE_FIELD3,
}

crud = CRUD('test', (FIELD1, FIELD2), {
    FIELD1: str,
    FIELD2: str,
    FIELD3: str,
})

@pytest.fixture(scope='function')
def temp_record():
    _id = crud.create(SAMPLE_RECORD)
    yield _id
    try:
        crud.delete((SAMPLE_FIELD1, SAMPLE_FIELD2))
    except ValueError:
        print('The record was already deleted.')


class TestLength:
    def test_basic(self):
        old_length = crud.length()
        _id = crud.create(SAMPLE_RECORD)
        assert crud.length() == old_length + 1
        crud.delete(SAMPLE_KEY)
        assert crud.length() == old_length


class TestCreate:
    def test_valid(self):
        _id = crud.create(SAMPLE_RECORD)
        assert common.is_valid_id(_id)
        records = crud.read()
        assert SAMPLE_KEY in records
        crud.delete(SAMPLE_KEY)

    def test_non_dict(self):
        with pytest.raises(ValueError):
            crud.create(10)

    def test_missing_key(self):
        with pytest.raises(ValueError):
            crud.create({FIELD1: SAMPLE_FIELD1})


class TestRead:
    def test_basic(self, temp_record):
        records = crud.read()
        assert isinstance(records, dict)
        assert SAMPLE_KEY in records
        assert len(records) > 0


class TestUpdate:
    def test_basic(self):
        _id = crud.create(SAMPLE_RECORD)
        new_field1 = 'new_field1'
        new_key = (new_field1, SAMPLE_FIELD2)
        crud.update(SAMPLE_KEY, {FIELD1: new_field1})
        records = crud.read()
        new_record = records[new_key]

        assert new_key in records
        assert new_record[FIELD1] == new_field1
        assert new_record[FIELD2] == SAMPLE_FIELD2
        assert new_record[FIELD3] == SAMPLE_FIELD3
        crud.delete(new_key)

    def test_non_dict(self):
        with pytest.raises(ValueError):
            crud.update(SAMPLE_KEY, 123)

    def test_invalid_key(self):
        with pytest.raises(KeyError):
            crud.update((SAMPLE_FIELD1), {})


class TestDelete:
    def test_basic(self):
        _id = crud.create(SAMPLE_RECORD)
        records = crud.read()
        assert SAMPLE_KEY in records
        crud.delete(SAMPLE_KEY)
        records = crud.read()
        assert SAMPLE_KEY not in records

    def test_invalid_key(self):
        with pytest.raises(KeyError):
            crud.delete((SAMPLE_FIELD1))
