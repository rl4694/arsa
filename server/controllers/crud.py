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


class CRUD:
    def __init__(self, collection: str, keys: tuple, attributes: dict):
        # Validate parameters
        if not isinstance(collection, str):
            raise ValueError('collection must be a string')
        for key in keys:
            if key not in attributes:
                raise ValueError(f'{key} not in attributes')

        self.collection = collection
        self.attributes = attributes
        self.keys = tuple(keys)
        self.cache = Cache(collection, self.keys)

    def get_cache_key(self, fields: dict):
        cache_key = []
        for key in self.keys:
            if not fields.get(key):
                raise ValueError(f'{key} missing in fields: {fields}')
            value = fields[key]
            if self.attributes[key] == str and isinstance(fields[key], str):
                value = fields[key].strip().lower()
            cache_key.append(value)
        return tuple(cache_key)

    def get_db_key(self, query: tuple):
        db_key = {}
        for i, key in enumerate(self.keys):
            db_key[key] = query[i]
        return db_key

    def length(self) -> int:
        return len(self.cache.read())

    def create(self, fields: dict, recursive: bool = True) -> str:
        if not isinstance(fields, dict):
            raise ValueError(f'Bad type for fields: {type(fields)}')

        key = self.get_cache_key(fields)
        store = self.cache.read()

        if key in store:
            if recursive:
                return str(store[key]['_id'])
            else:
                raise ValueError('Duplicate detected and recursive not allowed.')

        result = dbc.create(self.collection, fields)
        # refresh cache after mutations
        self.cache.reload()
        if not result or not getattr(result, 'inserted_id', None):
            raise RuntimeError('Create failed: no inserted_id')
        return str(result.inserted_id)

    def read(self) -> dict:
        return self.cache.read()

    def read_one_by_id(self, id_or_str) -> Optional[dict]:
        oid = self._ensure_objectid(id_or_str)
        return dbc.read_one(self.collection, {'_id': oid})

    def update(self, query: tuple, data: dict):
        if not isinstance(data, dict):
            raise ValueError(f'Bad type for data: {type(data)}')
        
        result = dbc.update(self.collection, self.get_db_key(query), data)
        if not result or getattr(result, 'matched_count', 0) == 0:
            raise KeyError(f'Record not found: {query}')
        self.cache.reload()

    def delete(self, query: tuple):
        deleted = dbc.delete(self.collection, self.get_db_key(query))
        if deleted == 0:
            raise KeyError(f'Record not found: {query}')
        self.cache.reload()
