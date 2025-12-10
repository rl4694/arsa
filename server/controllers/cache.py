"""
Caching for data controllers.
"""

import data.db_connect as dbc
import time
from typing import Optional


class Cache:
    def __init__(self, collection: str):
        """
        Validate and initialize the cache parameters.
        """
        # Check if arguments are valid
        if not isinstance(collection, str):
            raise ValueError(f'Bad type for collection: {type(collection)}')

        # Initialize members
        self.collection = collection
        self.data = None

    def reload(self):
        """
        Reload cache by reading from MongoDB.
        """
        self.data = {}
        records = dbc.read(self.collection, no_id=False) or []
        for record in records:
            self.data[record.get('_id')] = record

    def read(self) -> dict:
        """
        Return the cached data. This reloads the cache if it is uninitialized.
        """
        if self.data is None:
            self.reload()
        return self.data
