"""
This file implements caching for the data controllers.
"""

import data.db_connect as dbc
from functools import wraps

# TODO: add tests to cache
class Cache:
    def __init__(self, collection: str, keys: tuple):
        """
        Initialize a cache for a MongoDB collection.

        Args:
            collection: name of the collection to cache
            keys: field names that make up the cache key
        """
        if not isinstance(collection, str):
            raise ValueError(f'Bad type for collection: {type(collection)}')
        try:
            iter(keys)
        except:
            raise ValueError(f'Keys is not iterable: {type(keys)}')

        self.collection = collection
        self.keys = keys
        self.data = None


    def reload(self):
        """
        Reload the data stored in the cache using MongoDB.
        """
        self.data = {}
        records = dbc.read(self.collection, no_id=False)
        for record in records:
            primary_key = []
            for key in self.keys:
                primary_key.append(record.get(key))
            self.data[tuple(primary_key)] = record


    def needs_cache(self, func):
        """
        Decorate to ensure cache exists before executing function.
        Automatically calls reload() if cache is uninitialized.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.data:
                self.reload()
            return func(*args, **kwargs)
        return wrapper