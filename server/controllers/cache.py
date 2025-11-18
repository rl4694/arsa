"""
Caching for data controllers.
"""

import data.db_connect as dbc
from functools import wraps
import time
from typing import Optional, Any


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
        self.stats = {
            'hits': 0,
            'misses': 0,
            'reloads': 0,
        }

    def reload(self):
        self.data = {}
        records = dbc.read(self.collection, no_id=False)
        for record in records:
            primary_key = []
            for key in self.keys:
                primary_key.append(record.get(key))
            self.data[tuple(primary_key)] = record
        
        self.last_reload = time.time()
        self.stats['reloads'] += 1
    
    def is_expired(self) -> bool:
        if self.data is None or self.last_reload is None:
            return True
        if self.ttl is None:
            return False
        return (time.time() - self.last_reload) > self.ttl

    def read(self) -> dict:
        if self.is_expired():
            self.reload()
        return self.data
    
    def get(self, *key_values) -> Optional[dict]:
        data = self.read()
        key = tuple(key_values)
        
        if key in data:
            self.stats['hits'] += 1
            return data[key]
        else:
            self.stats['misses'] += 1
            return None
    
    def get_stats(self) -> dict:
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        return {
            **self.stats,
            'total_requests': total_requests,
            'hit_rate': round(hit_rate, 2),
            'size': len(self.data) if self.data else 0,
            'last_reload': self.last_reload,
            'ttl': self.ttl,
            'is_expired': self.is_expired()
        }
    
    def reset_stats(self):
        self.stats = {
            'hits': 0,
            'misses': 0,
            'reloads': self.stats['reloads'],
        }
    
    def clear(self):
        self.data = None
        self.last_reload = None
    
    def read_flat(self) -> dict:
        data = self.read()
        if len(self.keys) == 1:
            return {key[0]: value for key, value in data.items()}
        return data
