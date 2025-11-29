"""
Caching for data controllers.
"""

import data.db_connect as dbc
import time
from typing import Optional


class Cache:
    def __init__(self, collection: str, keys: tuple):
        # Check if arguments are valid
        if not isinstance(collection, str):
            raise ValueError(f'Bad type for collection: {type(collection)}')
        try:
            iter(keys)
        except TypeError:
            raise ValueError(f'Keys is not iterable: {type(keys)}')

        # Initialize members
        self.collection = collection
        self.keys = keys
        self.data = None

    def reload(self):
        """
        Reload cache by reading from MongoDB.
        """
        self.data = {}
        records = dbc.read(self.collection, no_id=False) or []
        for record in records:
            # Build primary key
            primary_key = []
            for key in self.keys:
                primary_key.append(record.get(key))
            # Add record (identified by its primary key) to the cache
            self.data[tuple(primary_key)] = record

    def read(self) -> dict:
        """
        Return the cached data. This reloads the cache if it is uninitialized.
        """
        if self.data is None:
            self.reload()
        return self.data
