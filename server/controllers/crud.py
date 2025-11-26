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


class CRUDController:
    def __init__(self, collection: str, key_fields: Iterable[str], *,
                 required_fields: Optional[Iterable[str]] = None,
                 normalize_fields: Optional[Iterable[str]] = None,
                 ttl: Optional[float] = None):
        if not isinstance(collection, str):
            raise ValueError('collection must be a string')
        try:
            iter(key_fields)
        except TypeError:
            raise ValueError('key_fields must be iterable')

        self.collection = collection
        self.key_fields = tuple(key_fields)
        self.required_fields = tuple(required_fields) if required_fields else ()
        self.normalize_fields = tuple(normalize_fields) if normalize_fields else ()
        self.cache = Cache(collection, self.key_fields, ttl)

    def _normalize(self, fields: dict) -> dict:
        out = {}
        for k, v in fields.items():
            if k in self.normalize_fields and isinstance(v, str):
                out[k] = v.strip().lower()
            else:
                out[k] = v
        return out

    def _key_from_fields(self, fields: dict) -> Tuple:
        nf = self._normalize(fields)
        return tuple(nf.get(k) for k in self.key_fields)

    def length(self) -> int:
        return len(self.cache.read())

    def create(self, fields: dict, recursive: bool = True) -> str:
        if not isinstance(fields, dict):
            raise ValueError(f'Bad type for fields: {type(fields)}')
        for r in self.required_fields:
            if not fields.get(r):
                raise ValueError(f'{r} missing in fields: {fields.get(r)}')

        normalized = self._normalize(fields)
        key = self._key_from_fields(normalized)
        store = self.cache.read()

        if key in store:
            if recursive:
                return str(store[key]['_id'])
            else:
                raise ValueError('Duplicate detected and recursive not allowed.')

        result = dbc.create(self.collection, normalized)
        # refresh cache after mutations
        self.cache.reload()
        if not result or not getattr(result, 'inserted_id', None):
            raise RuntimeError('Create failed: no inserted_id')
        return str(result.inserted_id)

    def read(self) -> dict:
        return self.cache.read()

    def read_one_by_id(self, id_str: str) -> Optional[dict]:
        return dbc.read_one(self.collection, {'_id': ObjectId(id_str)})

    def update(self, id_str: str, data: dict):
        if not isinstance(data, dict):
            raise ValueError(f'Bad type for data: {type(data)}')
        result = dbc.update(self.collection, {'_id': ObjectId(id_str)}, data)
        if not result or getattr(result, 'matched_count', 0) == 0:
            raise KeyError('Record not found')
        self.cache.reload()

    def delete(self, id_str: str):
        deleted = dbc.delete(self.collection, {'_id': ObjectId(id_str)})
        if deleted == 0:
            raise KeyError('Record not found')
        self.cache.reload()
