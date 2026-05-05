# server/controllers/tests/test_crud.py
import pytest
from server.controllers.crud import is_valid_id, validate_coordinates, CRUD

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


class TestIsValidId:
    def test_basic(self):
        is_valid = is_valid_id('64c13ab08edf48a008793cac')
        assert is_valid == True
    
    def test_invalid_id(self):
        is_valid = is_valid_id('invalid')
        assert is_valid == False


class TestFindDuplicate:
    def test_duplicate(self, temp_record):
        duplicate = crud.find_duplicate(SAMPLE_RECORD)
        assert duplicate['_id'] == temp_record

    def test_no_duplicate(self):
        duplicate = crud.find_duplicate(SAMPLE_RECORD)
        assert duplicate is None

    def test_excluded_id(self, temp_record):
        duplicate = crud.find_duplicate(SAMPLE_RECORD, excluded_id=temp_record)
        assert duplicate is None

    def test_bad_fields(self):
        with pytest.raises(ValueError):
            crud.find_duplicate(123)
    
    def test_bad_search_list(self):
        with pytest.raises(ValueError):
            crud.find_duplicate(SAMPLE_RECORD, search_list=123)

    def test_bad_excluded_id(self):
        with pytest.raises(ValueError):
            crud.find_duplicate(SAMPLE_RECORD, excluded_id=123)


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


class TestCreateMany:
    def test_valid(self):
        SAMPLE_RECORD2 = {
            FIELD1: "another1",
            FIELD2: "another2",
            FIELD3: "another3",
        }
        _ids = crud.create_many([SAMPLE_RECORD, SAMPLE_RECORD2])
        records = crud.read()
        for _id in _ids:
            assert is_valid_id(_id)
            assert _id in records
            crud.delete(_id)

    def test_bad_fields_list_type(self):
        with pytest.raises(ValueError):
            crud.create_many(123)

    def test_bad_fields_type(self):
        with pytest.raises(ValueError):
            crud.create_many([123])

    def test_bad_field_type(self):
        with pytest.raises(ValueError):
            crud.create_many([{FIELD1: SAMPLE_FIELD1, FIELD2: 123}])

    def test_missing_field(self):
        _id = crud.create_many([{FIELD1: SAMPLE_FIELD1, FIELD2: SAMPLE_FIELD2}])[0]
        assert is_valid_id(_id)
        record = crud.read()[_id]
        assert record[FIELD1] == SAMPLE_FIELD1
        assert record[FIELD2] == SAMPLE_FIELD2
        assert record[FIELD3] == None
        assert FIELD3 in record
        crud.delete(_id)

    def test_existing_duplicate(self, temp_record):
        with pytest.raises(ValueError):
            crud.create_many([SAMPLE_RECORD])

    def test_new_duplicate(self):
        with pytest.raises(ValueError):
            crud.create_many([SAMPLE_RECORD, SAMPLE_RECORD])


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

    def test_non_key_field(self):
        _id = crud.create(SAMPLE_RECORD)
        new_field3 = 'new_field3'
        crud.update(_id, {FIELD3: new_field3})
        records = crud.read()
        new_record = records[_id]

        assert _id in records
        assert new_record[FIELD1] == SAMPLE_FIELD1
        assert new_record[FIELD2] == SAMPLE_FIELD2
        assert new_record[FIELD3] == new_field3
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
        num_deleted = crud.delete(_id)
        records = crud.read()
        assert _id not in records
        assert num_deleted > 0

    def test_invalid_id(self):
        with pytest.raises(ValueError):
            crud.delete(123)

class TestValidateCoordinates:
    def test_valid_coordinates_boundaries(self):
        validate_coordinates(-180.0, 180.0)

    def test_invalid_latitude_out_of_range(self):
        with pytest.raises(ValueError, match='Latitude'):
            validate_coordinates(181.0, 180.0)

    def test_invalid_longitude_out_of_range(self):
        with pytest.raises(ValueError, match='Longitude'):
            validate_coordinates(0.0, -181.0)
