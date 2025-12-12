# server/controllers/tests/test_crud.py
import pytest
from server.controllers.crud import is_valid_id
from server.controllers.crud import CRUD

FIELD1 = 'field1'
FIELD2 = 'field2'
FIELD3 = 'field3'
SAMPLE_FIELD1 = 'sample1'
SAMPLE_FIELD2 = 'sample2'
SAMPLE_FIELD3 = 'sample3'
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
        crud.delete(_id)
    except ValueError:
        print('The record was already deleted.')


class TestFindDuplicate:
    def test_duplicate(self, temp_record):
        duplicate = crud.find_duplicate(SAMPLE_RECORD)
        assert duplicate['_id'] == temp_record

    def test_no_duplicate(self):
        duplicate = crud.find_duplicate(SAMPLE_RECORD)
        assert duplicate is None

    def test_non_dict(self):
        with pytest.raises(ValueError):
            crud.find_duplicate(123)


class TestCreate:
    def test_valid(self):
        _id = crud.create(SAMPLE_RECORD)
        assert is_valid_id(_id)
        records = crud.read()
        assert _id in records
        record = records[_id]
        assert record[FIELD1] == SAMPLE_FIELD1
        assert record[FIELD2] == SAMPLE_FIELD2
        assert record[FIELD3] == SAMPLE_FIELD3
        crud.delete(_id)

    def test_bad_recursive_type(self):
        with pytest.raises(ValueError):
            crud.create(SAMPLE_RECORD, 123)

    def test_bad_fields_type(self):
        with pytest.raises(ValueError):
            crud.create(123)

    def test_bad_field_type(self):
        with pytest.raises(ValueError):
            crud.create({FIELD1: SAMPLE_FIELD1, FIELD2: 123})


class TestCount:
    def test_basic(self):
        old_count = crud.count()
        _id = crud.create(SAMPLE_RECORD)
        assert crud.count() == old_count + 1
        crud.delete(_id)
        assert crud.count() == old_count


class TestRead:
    def test_basic(self, temp_record):
        records = crud.read()
        assert isinstance(records, dict)
        assert temp_record in records
        assert len(records) > 0


class TestSelect:
    def test_basic(self, temp_record):
        record = crud.select(temp_record)
        assert record[FIELD1] == SAMPLE_FIELD1
        assert record[FIELD2] == SAMPLE_FIELD2
        assert record[FIELD3] == SAMPLE_FIELD3

    def test_invalid_id(self):
        with pytest.raises(ValueError):
            record = crud.select(123)


class TestUpdate:
    def test_basic(self):
        _id = crud.create(SAMPLE_RECORD)
        new_field1 = 'new_field1'
        crud.update(_id, {FIELD1: new_field1})
        records = crud.read()
        new_record = records[_id]

        assert _id in records
        assert new_record[FIELD1] == new_field1
        assert new_record[FIELD2] == SAMPLE_FIELD2
        assert new_record[FIELD3] == SAMPLE_FIELD3
        crud.delete(_id)

    def test_non_dict(self, temp_record):
        with pytest.raises(ValueError):
            crud.update(temp_record, 123)

    def test_invalid_id(self):
        with pytest.raises(ValueError):
            crud.update(123, {})


class TestDelete:
    def test_basic(self):
        _id = crud.create(SAMPLE_RECORD)
        records = crud.read()
        assert _id in records
        crud.delete(_id)
        records = crud.read()
        assert _id not in records

    def test_invalid_id(self):
        with pytest.raises(ValueError):
            crud.delete(123)
