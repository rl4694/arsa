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

    def find_duplicate(self, fields: dict):
        if not isinstance(fields, dict):
            raise ValueError(f'Bad type for fields: {type(fields)}')

        records = self.cache.read()
        for record in records.values():
            # Check if all key fields from current record and query match
            if all(fields.get(key) == record.get(key) for key in self.keys):
                return record
        return None

    def create(self, fields: dict, return_duplicate_id: bool = True) -> str:
        """
        Create a new record from the provided fields.
        """
        # Validate parameters
        self.validate(fields)
        if not isinstance(return_duplicate_id, bool):
            rdi_type = type(return_duplicate_id)
            raise ValueError(f'Bad type for return_duplicate_id: {rdi_type}')
        
        # Build the record from the fields
        new_record = {}
        for attribute in self.attributes:
            new_record[attribute] = fields.get(attribute)

        # Check if record already exists
        duplicate = self.find_duplicate(fields)
        if duplicate:
            if return_duplicate_id:
                return str(duplicate['_id'])
            else:
                raise ValueError('Duplicate detected.')

        # Create the record
        result = dbc.create(self.collection, new_record)
        if not result or not getattr(result, 'inserted_id', None):
            raise RuntimeError('Create failed: no inserted_id')
        self.cache.reload()
        return str(result.inserted_id)

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
        if self.find_duplicate(fields):
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

        deleted = dbc.delete(self.collection, {'_id': ObjectId(_id)})
        if deleted == 0:
            raise KeyError(f'Record not found: {_id}')
        self.cache.reload()
