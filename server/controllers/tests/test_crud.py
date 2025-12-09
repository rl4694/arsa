# server/controllers/tests/test_crud.py
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
        crud.delete(_id)
    except ValueError:
        print('The record was already deleted.')


class TestCreate:
    def test_valid(self):
        _id = crud.create(SAMPLE_RECORD)
        assert common.is_valid_id(_id)
        records = crud.read()
        assert SAMPLE_KEY in records
        record = records[SAMPLE_KEY]
        assert record[FIELD1] == SAMPLE_FIELD1
        assert record[FIELD2] == SAMPLE_FIELD2
        assert record[FIELD3] == SAMPLE_FIELD3
        crud.delete(_id)

    @pytest.mark.skip(reason="Cache keys will be replaced with _id soon.")
    def test_non_normalized_key(self):
        key = ('first', 'sec ond.')
        _id = crud.create({FIELD1: ' FIRST  ', FIELD2: ' Sec ond. ' })
        assert common.is_valid_id(_id)
        records = crud.read()
        assert key in records
        record = records[key]
        assert record[FIELD1] == 'first'
        assert record[FIELD2] == 'sec ond.'
        crud.delete(_id)

    def test_empty_key(self):
        key = (SAMPLE_FIELD1, '')
        _id = crud.create({FIELD1: SAMPLE_FIELD1, FIELD2: '' })
        assert common.is_valid_id(_id)
        records = crud.read()
        assert key in records
        record = records[key]
        assert record[FIELD1] == SAMPLE_FIELD1
        assert record[FIELD2] == ''
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

    def test_missing_key(self):
        with pytest.raises(KeyError):
            crud.create({FIELD1: SAMPLE_FIELD1})


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
        assert SAMPLE_KEY in records
        assert len(records) > 0


class TestSelect:
    def test_basic(self, temp_record):
        record = crud.select(temp_record)
        assert record[FIELD1] == SAMPLE_FIELD1
        assert record[FIELD2] == SAMPLE_FIELD2
        assert record[FIELD3] == SAMPLE_FIELD3

    def test_invalid_id(self):
        with pytest.raises(ValueError):
            record = crud.select('invalid')


class TestUpdate:
    def test_basic(self):
        _id = crud.create(SAMPLE_RECORD)
        new_field1 = 'new_field1'
        new_key = (new_field1, SAMPLE_FIELD2)
        crud.update(_id, {FIELD1: new_field1})
        records = crud.read()
        new_record = records[new_key]

        assert new_key in records
        assert new_record[FIELD1] == new_field1
        assert new_record[FIELD2] == SAMPLE_FIELD2
        assert new_record[FIELD3] == SAMPLE_FIELD3
        crud.delete(_id)

    def test_non_normalized_key(self):
        _id = crud.create(SAMPLE_RECORD)
        new_key = ('first.', SAMPLE_FIELD2)
        crud.update(_id, {FIELD1: ' First. '})
        records = crud.read()
        new_record = records[new_key]

        assert new_key in records
        assert new_record[FIELD1] == 'first.'
        assert new_record[FIELD2] == SAMPLE_FIELD2
        assert new_record[FIELD3] == SAMPLE_FIELD3
        crud.delete(_id)

    def test_non_dict(self, temp_record):
        with pytest.raises(ValueError):
            crud.update(temp_record, 123)

    def test_invalid_key(self):
        with pytest.raises(ValueError):
            crud.update(123, {})


class TestDelete:
    def test_basic(self):
        _id = crud.create(SAMPLE_RECORD)
        records = crud.read()
        assert SAMPLE_KEY in records
        crud.delete(_id)
        records = crud.read()
        assert SAMPLE_KEY not in records

    def test_invalid_key(self):
        with pytest.raises(ValueError):
            crud.delete(123)
