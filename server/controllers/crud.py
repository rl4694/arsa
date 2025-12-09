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
import server.common as common
import data.db_connect as dbc


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
        self.keys = tuple(keys)
        self.attributes = attributes
        self.cache = Cache(self.collection, self.keys)

    def create(self, fields: dict, recursive: bool = True) -> str:
        """
        Create a new record from the provided fields.
        """
        # Validate parameters
        if not isinstance(fields, dict):
            raise ValueError(f'Bad type for fields: {type(fields)}')
        if not isinstance(recursive, bool):
            raise ValueError(f'Bad type for recursive: {type(recursive)}')
        
        # Build the record from the fields
        new_record = {}
        cache_key = []
        for attribute in self.attributes:
            field = fields.get(attribute)
            # Validate the field
            is_valid_type = isinstance(field, self.attributes[attribute])
            if field is not None and not is_valid_type:
                raise ValueError(f'Bad type for field {field}: {type(field)}')
            if attribute in self.keys:
                if field is None:
                    raise KeyError(f'Missing required field: {attribute}')
                # Side effect that will likely be removed soon
                # if isinstance(field, str):
                #     field = field.strip().lower()
                cache_key.append(field)
            # Add the field
            new_record[attribute] = field

        # Check if record already exists
        cache_key = tuple(cache_key)
        store = self.cache.read()
        if cache_key in store:
            if recursive:
                return str(store[cache_key]['_id'])
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
        if not common.is_valid_id(_id):
            raise ValueError(f'Invalid id: {_id}')
        records = self.cache.read()
        for record in records.values():
            if record['_id'] == _id:
                return record
        raise KeyError(f'Record not found: {query}')

    def update(self, _id: str, fields: dict):
        """
        Update the fields for the record matching the query.
        """
        if not isinstance(fields, dict):
            raise ValueError(f'Bad type for data: {type(fields)}')
        if not common.is_valid_id(_id):
            raise ValueError(f'Invalid id: {_id}')

        # Build the record from the fields
        record = {}
        for attribute in self.attributes:
            field = fields.get(attribute)
            if field is None:
                continue
            if not isinstance(field, self.attributes[attribute]):
                raise ValueError(f'Bad type for field {field}: {type(field)}')
            if attribute in self.keys and isinstance(field, str):
                field = field.strip().lower()
            record[attribute] = field

        # Update the record
        result = dbc.update(self.collection, {'_id': ObjectId(_id)}, record)
        if not result or getattr(result, 'matched_count', 0) == 0:
            raise KeyError(f'Record not found: {_id}')
        self.cache.reload()

    def delete(self, _id: str):
        """
        Delete the record matching the query.
        """
        if not common.is_valid_id(_id):
            raise ValueError(f'Invalid id: {_id}')

        deleted = dbc.delete(self.collection, {'_id': ObjectId(_id)})
        if deleted == 0:
            raise KeyError(f'Record not found: {_id}')
        self.cache.reload()
