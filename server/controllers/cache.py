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
    

    def read(self):
        """
        Return the data stored in the cache.
        """
        if self.data is None:
            self.reload()
        return self.data
