"""
Caching for data controllers.
"""

import data.db_connect as dbc
import time
from typing import Optional


class Cache:
    def __init__(self, collection: str, keys: tuple, ttl: Optional[float] = None):
        if not isinstance(collection, str):
            raise ValueError(f'Bad type for collection: {type(collection)}')
        try:
            iter(keys)
        except:
            raise ValueError(f'Keys is not iterable: {type(keys)}')

        self.collection = collection
        self.keys = keys
        self.data = None
        self.ttl = ttl
        self.last_reload = None

    def reload(self):
        self.data = {}
        records = dbc.read(self.collection, no_id=False)
        for record in records:
            primary_key = []
            for key in self.keys:
                primary_key.append(record.get(key))
            self.data[tuple(primary_key)] = record
        
        self.last_reload = time.time()
    
    def read(self) -> dict:
        if self.data is None:
            self.reload()
        return self.data
    
