"""
Reusable CRUD controller for data controllers.

This class centralizes common behaviors used by the `cities`, `states`,
and `nations` controllers: cache-backed read, create with duplicate
checking based on key fields, and id-based update/delete that reload the
cache after writes.
"""
from typing import Iterable, Optional, Tuple
from bson.objectid import ObjectId
from server.controllers.cache import Cache
import data.db_connect as dbc


def is_valid_id(_id: str) -> bool:
    """Return whether _id is a valid document id"""
    return isinstance(_id, str) and ObjectId.is_valid(_id)


class CRUD:
    def __init__(self, collection: str, keys: tuple, attributes: dict):
        # Validate parameters
        if not isinstance(collection, str):
            raise ValueError('collection must be a string')
        for key in keys:
            if key not in attributes:
                raise ValueError(f'{key} not in attributes')

        # Intialize members
        self.collection = collection
        self.keys = keys
        self.attributes = attributes
        self.cache = Cache(self.collection)

    def validate(self, fields: dict):
        # Check whether fields is the correct type
        if not isinstance(fields, dict):
            raise ValueError(f'Bad type for fields: {type(fields)}')

        # Check whether each individual field is the correct type
        for attribute in self.attributes:
            field = fields.get(attribute)
            is_valid_type = isinstance(field, self.attributes[attribute])
            if field is not None and not is_valid_type:
                raise ValueError(f'Bad type for field {field}: {type(field)}')

    def find_duplicate(self, fields: dict, search_list: list = None, excluded_id: str = ''):
        """
        Find a record with the same key fields as the provided record fields.
        - search_list: list of records to search from. Defaults to the cache
        - excluded_id: _id of the record to exclude from the duplicate search
        """
        if not isinstance(fields, dict):
            raise ValueError(f'Bad type for fields: {type(fields)}')
        if not isinstance(search_list, list):
            if search_list is None:
                search_list = list(self.cache.read().values())
            else:
                raise ValueError(f'Bad type for search_list: {type(search_list)}')
        if not isinstance(excluded_id, str):
            raise ValueError(f'Bad type for fields: {type(excluded_id)}')

        for record in search_list:
            # Check if all key fields from current record and query match
            has_matching_keys = all(fields.get(key) == record.get(key) for key in self.keys)
            if record.get('_id') != excluded_id and has_matching_keys:
                return record
        return None

    def create(self, fields: dict) -> str:
        """
        Create a new record from the provided fields.
        """
        return self.create_many([fields])[0]

    def create_many(self, fields_list: list) -> list:
        """
        Create a list of records from the provided fields list. Faster than
        create() for multiple records because this batches the database
        calls into a single network request.
        """
        # Validate parameters
        if not isinstance(fields_list, list):
            raise ValueError(f'Bad type for fields_list: {type(fields_list)}')

        new_records = []
        dup_search_list = list(self.cache.read().values())
        for fields in fields_list:
            # Validate the fields
            self.validate(fields)
            # Build the record from the fields
            new_record = {}
            for attribute in self.attributes:
                new_record[attribute] = fields.get(attribute)
                if self.find_duplicate(fields, search_list=dup_search_list):
                    raise ValueError('Duplicate detected.')
            # Add the record to the lists
            new_records.append(new_record)
            dup_search_list.append(new_record)

        # Create the records list
        result = dbc.create_many(self.collection, new_records)
        if not result or not getattr(result, 'inserted_ids', None):
            raise RuntimeError('Create failed: no inserted_ids')
        self.cache.reload()
        return [str(_id) for _id in result.inserted_ids]

    def count(self) -> int:
        """
        Return the number of records in the collection
        """
        return len(self.cache.read())

    def read(self) -> dict:
        """
        Return all records in the collection.
        """
        return self.cache.read()

    def select(self, _id: str) -> dict:
        """
        Return a record matching the query.
        """
        if not is_valid_id(_id):
            raise ValueError(f'Invalid id: {_id}')
        records = self.cache.read()
        if _id in records:
            return records[_id]
        raise KeyError(f'Record not found: {query}')

    def update(self, _id: str, fields: dict):
        """
        Update the fields for the record matching the query.
        """
        # Validate parameters
        self.validate(fields)
        if not is_valid_id(_id):
            raise ValueError(f'Invalid id: {_id}')

        # Build the record from the fields
        record = {}
        for attribute in self.attributes:
            field = fields.get(attribute)
            if field is not None:
                record[attribute] = field

        # Check if updated fields is a duplicate
        if self.find_duplicate(fields, excluded_id=_id):
            raise ValueError('Duplicate detected.')

        # Update the record
        result = dbc.update(self.collection, {'_id': ObjectId(_id)}, record)
        if not result or getattr(result, 'matched_count', 0) == 0:
            raise KeyError(f'Record not found: {_id}')
        self.cache.reload()

    def delete(self, _id: str):
        """
        Delete the record matching the query.
        """
        if not is_valid_id(_id):
            raise ValueError(f'Invalid id: {_id}')

        num_deleted = dbc.delete(self.collection, {'_id': ObjectId(_id)})
        if num_deleted == 0:
            raise KeyError(f'Record not found: {_id}')
        self.cache.reload()
        return num_deleted
