"""
Advanced tests for Cache class features (TTL, statistics, etc).
"""
import pytest
import time
from unittest.mock import patch, MagicMock
from server.controllers.cache import Cache


class TestCacheTTL:
    """Test Cache TTL (time-to-live) functionality."""
    
    def test_init_with_ttl(self):
        """Test initializing cache with TTL."""
        cache = Cache('test_collection', ('name',), ttl=60.0)
        assert cache.ttl == 60.0
    
    def test_init_without_ttl(self):
        """Test initializing cache without TTL."""
        cache = Cache('test_collection', ('name',))
        assert cache.ttl is None
    
    @patch('server.controllers.cache.dbc.read')
    def test_is_expired_before_first_load(self, mock_read):
        """Test that cache is expired before first load."""
        cache = Cache('test_collection', ('name',), ttl=60.0)
        assert cache.is_expired() is True
    
    @patch('server.controllers.cache.dbc.read')
    def test_is_expired_after_load_no_ttl(self, mock_read):
        """Test that cache without TTL never expires."""
        mock_read.return_value = [{'_id': '1', 'name': 'test'}]
        cache = Cache('test_collection', ('name',))
        cache.reload()
        
        assert cache.is_expired() is False
    
    @patch('server.controllers.cache.dbc.read')
    @patch('server.controllers.cache.time.time')
    def test_is_expired_within_ttl(self, mock_time, mock_read):
        """Test that cache is not expired within TTL period."""
        mock_read.return_value = [{'_id': '1', 'name': 'test'}]
        mock_time.return_value = 1000.0
        
        cache = Cache('test_collection', ('name',), ttl=60.0)
        cache.reload()
        
        # Check immediately after reload (within TTL)
        mock_time.return_value = 1030.0  # 30 seconds later
        assert cache.is_expired() is False
    
    @patch('server.controllers.cache.dbc.read')
    @patch('server.controllers.cache.time.time')
    def test_is_expired_after_ttl(self, mock_time, mock_read):
        """Test that cache is expired after TTL period."""
        mock_read.return_value = [{'_id': '1', 'name': 'test'}]
        mock_time.return_value = 1000.0
        
        cache = Cache('test_collection', ('name',), ttl=60.0)
        cache.reload()
        
        # Check after TTL expires
        mock_time.return_value = 1061.0  # 61 seconds later
        assert cache.is_expired() is True
    
    @patch('server.controllers.cache.dbc.read')
    @patch('server.controllers.cache.time.time')
    def test_auto_reload_on_expiry(self, mock_time, mock_read):
        """Test that cache automatically reloads when expired."""
        initial_data = [{'_id': '1', 'name': 'test1'}]
        updated_data = [{'_id': '1', 'name': 'test1'}, {'_id': '2', 'name': 'test2'}]
        
        mock_read.return_value = initial_data
        mock_time.return_value = 1000.0
        
        cache = Cache('test_collection', ('name',), ttl=60.0)
        
        # First read
        data = cache.read()
        assert len(data) == 1
        assert mock_read.call_count == 1
        
        # Read within TTL (should not reload)
        mock_time.return_value = 1030.0
        data = cache.read()
        assert len(data) == 1
        assert mock_read.call_count == 1  # No additional call
        
        # Read after TTL expires (should reload)
        mock_read.return_value = updated_data
        mock_time.return_value = 1061.0
        data = cache.read()
        assert len(data) == 2
        assert mock_read.call_count == 2  # Reloaded


class TestCacheGet:
    """Test Cache.get() method for single record lookup."""
    
    @patch('server.controllers.cache.dbc.read')
    def test_get_existing_record_single_key(self, mock_read):
        """Test getting an existing record with single key."""
        mock_read.return_value = [
            {'_id': '1', 'name': 'california', 'nation': 'USA'},
            {'_id': '2', 'name': 'texas', 'nation': 'USA'}
        ]
        cache = Cache('states', ('name',))
        
        result = cache.get('california')
        assert result is not None
        assert result['name'] == 'california'
        assert result['nation'] == 'USA'
    
    @patch('server.controllers.cache.dbc.read')
    def test_get_nonexistent_record(self, mock_read):
        """Test getting a non-existent record returns None."""
        mock_read.return_value = [
            {'_id': '1', 'name': 'california', 'nation': 'USA'}
        ]
        cache = Cache('states', ('name',))
        
        result = cache.get('florida')
        assert result is None
    
    @patch('server.controllers.cache.dbc.read')
    def test_get_existing_record_multiple_keys(self, mock_read):
        """Test getting an existing record with multiple keys."""
        mock_read.return_value = [
            {'_id': '1', 'name': 'test', 'type': 'A', 'value': 100},
            {'_id': '2', 'name': 'test', 'type': 'B', 'value': 200}
        ]
        cache = Cache('test_collection', ('name', 'type'))
        
        result = cache.get('test', 'A')
        assert result is not None
        assert result['value'] == 100
        
        result = cache.get('test', 'B')
        assert result is not None
        assert result['value'] == 200
    
    @patch('server.controllers.cache.dbc.read')
    def test_get_updates_statistics(self, mock_read):
        """Test that get() updates hit/miss statistics."""
        mock_read.return_value = [
            {'_id': '1', 'name': 'california', 'nation': 'USA'}
        ]
        cache = Cache('states', ('name',))
        
        # Hit
        cache.get('california')
        assert cache.stats['hits'] == 1
        assert cache.stats['misses'] == 0
        
        # Miss
        cache.get('florida')
        assert cache.stats['hits'] == 1
        assert cache.stats['misses'] == 1
        
        # Another hit
        cache.get('california')
        assert cache.stats['hits'] == 2
        assert cache.stats['misses'] == 1


class TestCacheStatistics:
    """Test Cache statistics functionality."""
    
    @patch('server.controllers.cache.dbc.read')
    def test_initial_stats(self, mock_read):
        """Test initial statistics values."""
        cache = Cache('test_collection', ('name',))
        stats = cache.get_stats()
        
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['reloads'] == 0
        assert stats['total_requests'] == 0
        assert stats['hit_rate'] == 0
        assert stats['size'] == 0
    
    @patch('server.controllers.cache.dbc.read')
    def test_stats_after_operations(self, mock_read):
        """Test statistics after various operations."""
        mock_read.return_value = [
            {'_id': '1', 'name': 'test1'},
            {'_id': '2', 'name': 'test2'}
        ]
        cache = Cache('test_collection', ('name',))
        
        # Perform operations
        cache.get('test1')  # hit
        cache.get('test2')  # hit
        cache.get('test3')  # miss
        cache.get('test1')  # hit
        
        stats = cache.get_stats()
        assert stats['hits'] == 3
        assert stats['misses'] == 1
        assert stats['total_requests'] == 4
        assert stats['hit_rate'] == 75.0
        assert stats['size'] == 2
        assert stats['reloads'] == 1  # One automatic reload on first get
    
    @patch('server.controllers.cache.dbc.read')
    def test_stats_after_reload(self, mock_read):
        """Test that reload increments reload counter."""
        mock_read.return_value = []
        cache = Cache('test_collection', ('name',))
        
        cache.reload()
        cache.reload()
        cache.reload()
        
        stats = cache.get_stats()
        assert stats['reloads'] == 3
    
    @patch('server.controllers.cache.dbc.read')
    def test_reset_stats(self, mock_read):
        """Test resetting statistics."""
        mock_read.return_value = [{'_id': '1', 'name': 'test'}]
        cache = Cache('test_collection', ('name',))
        
        # Perform operations
        cache.get('test')
        cache.get('missing')
        cache.reload()
        
        assert cache.stats['hits'] == 1
        assert cache.stats['misses'] == 1
        assert cache.stats['reloads'] == 2
        
        # Reset stats
        cache.reset_stats()
        assert cache.stats['hits'] == 0
        assert cache.stats['misses'] == 0
        assert cache.stats['reloads'] == 2  # Reload count preserved
    
    @patch('server.controllers.cache.dbc.read')
    def test_stats_include_ttl_info(self, mock_read):
        """Test that stats include TTL information."""
        mock_read.return_value = []
        cache = Cache('test_collection', ('name',), ttl=60.0)
        cache.reload()
        
        stats = cache.get_stats()
        assert stats['ttl'] == 60.0
        assert 'last_reload' in stats
        assert stats['last_reload'] is not None
        assert 'is_expired' in stats
    
    @patch('server.controllers.cache.dbc.read')
    def test_hit_rate_zero_requests(self, mock_read):
        """Test hit rate calculation with zero requests."""
        cache = Cache('test_collection', ('name',))
        stats = cache.get_stats()
        assert stats['hit_rate'] == 0


class TestCacheClear:
    """Test Cache.clear() functionality."""
    
    @patch('server.controllers.cache.dbc.read')
    def test_clear(self, mock_read):
        """Test clearing cache data."""
        mock_read.return_value = [{'_id': '1', 'name': 'test'}]
        cache = Cache('test_collection', ('name',))
        
        # Load data
        cache.read()
        assert cache.data is not None
        assert cache.last_reload is not None
        
        # Clear
        cache.clear()
        assert cache.data is None
        assert cache.last_reload is None
    
    @patch('server.controllers.cache.dbc.read')
    def test_clear_preserves_stats(self, mock_read):
        """Test that clear preserves statistics."""
        mock_read.return_value = [{'_id': '1', 'name': 'test'}]
        cache = Cache('test_collection', ('name',))
        
        # Perform operations
        cache.get('test')
        cache.get('missing')
        
        old_stats = cache.stats.copy()
        
        # Clear should not affect stats
        cache.clear()
        assert cache.stats == old_stats
    
    @patch('server.controllers.cache.dbc.read')
    def test_read_after_clear(self, mock_read):
        """Test that read works after clear."""
        mock_read.return_value = [{'_id': '1', 'name': 'test'}]
        cache = Cache('test_collection', ('name',))
        
        # Load, clear, then read again
        cache.read()
        cache.clear()
        data = cache.read()
        
        assert data is not None
        assert ('test',) in data
        assert mock_read.call_count == 2  # Loaded twice


class TestCacheReadFlat:
    """Test Cache.read_flat() method for simplified key access."""
    
    @patch('server.controllers.cache.dbc.read')
    def test_read_flat_single_key(self, mock_read):
        """Test read_flat with single key returns flattened dict."""
        mock_read.return_value = [
            {'_id': '1', 'name': 'california', 'nation': 'USA'},
            {'_id': '2', 'name': 'texas', 'nation': 'USA'}
        ]
        cache = Cache('states', ('name',))
        
        result = cache.read_flat()
        
        # Should have string keys, not tuple keys
        assert 'california' in result
        assert 'texas' in result
        assert ('california',) not in result  # Tuple key should not exist
        
        # Values should be the records
        assert result['california']['nation'] == 'USA'
        assert result['texas']['nation'] == 'USA'
    
    @patch('server.controllers.cache.dbc.read')
    def test_read_flat_multiple_keys(self, mock_read):
        """Test read_flat with multiple keys returns tuple-keyed dict."""
        mock_read.return_value = [
            {'_id': '1', 'name': 'test', 'type': 'A', 'value': 100},
            {'_id': '2', 'name': 'test', 'type': 'B', 'value': 200}
        ]
        cache = Cache('test_collection', ('name', 'type'))
        
        result = cache.read_flat()
        
        # Should still have tuple keys for multi-key caches
        assert ('test', 'A') in result
        assert ('test', 'B') in result
        assert result[('test', 'A')]['value'] == 100
        assert result[('test', 'B')]['value'] == 200
    
    @patch('server.controllers.cache.dbc.read')
    def test_read_flat_empty_cache(self, mock_read):
        """Test read_flat with empty cache."""
        mock_read.return_value = []
        cache = Cache('states', ('name',))
        
        result = cache.read_flat()
        assert result == {}
    
    @patch('server.controllers.cache.dbc.read')
    def test_read_flat_none_key_value(self, mock_read):
        """Test read_flat handles None key values."""
        mock_read.return_value = [
            {'_id': '1', 'name': 'california'},
            {'_id': '2', 'value': 'no name'}  # Missing 'name' field
        ]
        cache = Cache('states', ('name',))
        
        result = cache.read_flat()
        
        # Should handle None as key
        assert 'california' in result
        assert None in result

