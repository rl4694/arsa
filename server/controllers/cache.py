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
        except TypeError:
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
            'total_requests': 0,
        }

    def reload(self):
        self.data = {}
        records = dbc.read(self.collection, no_id=False) or []
        for record in records:
            primary_key = []
            for key in self.keys:
                primary_key.append(record.get(key))
            self.data[tuple(primary_key)] = record
        
        self.last_reload = time.time()
        self.stats['reloads'] += 1
    
    def read(self) -> dict:
        if self.data is None:
            self.reload()
        elif self.is_expired():
            self.reload()
        return self.data

    def is_expired(self) -> bool:
        if self.last_reload is None:
            return True
        if self.ttl is None:
            return False
        return (time.time() - self.last_reload) > self.ttl
    
    def get(self, *key_values):
        if len(key_values) != len(self.keys):
            raise ValueError(f'Expected {len(self.keys)} key values, got {len(key_values)}')
        self.stats['total_requests'] += 1
        data = self.read()
        rec = data.get(tuple(key_values))

        if rec is None:
            self.stats['misses'] += 1
            return None

        self.stats['hits'] += 1
        return rec

    def get_stats(self) -> dict:
        hits = self.stats['hits']
        misses = self.stats['misses']
        reloads = self.stats['reloads']
        total = self.stats['total_requests']

        hit_rate = (hits * 100.0 / total) if total else 0

        return {
            'hits': hits,
            'misses': misses,
            'reloads': reloads,
            'total_requests': total,
            'hit_rate': hit_rate,
            'size': len(self.data) if self.data is not None else 0,
            'ttl': self.ttl,
            'last_reload': self.last_reload,
            'is_expired': self.is_expired(),
        }

    def reset_stats(self) -> None:
        self.stats['hits'] = 0
        self.stats['misses'] = 0
        self.stats['total_requests'] = 0

    def clear(self) -> None:
        self.data = None
        self.last_reload = None

    def read_flat(self) -> dict:
        data = self.read()
        if len(self.keys) == 1:
            flat = {}
            for k_tuple, rec in data.items():
                flat[k_tuple[0]] = rec
            return flat
        return dict(data)