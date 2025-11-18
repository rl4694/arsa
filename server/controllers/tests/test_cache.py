"""
Tests for the Cache class.
"""
import pytest
from unittest.mock import patch, MagicMock
from server.controllers.cache import Cache


class TestCacheInit:
    """Test Cache initialization."""
    
    def test_valid_init(self):
        """Test creating a cache with valid parameters."""
        cache = Cache('test_collection', ('name',))
        assert cache.collection == 'test_collection'
        assert cache.keys == ('name',)
        assert cache.data is None
    
    def test_invalid_collection_type(self):
        """Test that non-string collection raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            Cache(123, ('name',))
        assert 'Bad type for collection' in str(exc_info.value)
    
    def test_invalid_keys_type(self):
        """Test that non-iterable keys raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            Cache('test_collection', 123)
        assert 'Keys is not iterable' in str(exc_info.value)
    
    def test_multiple_keys(self):
        """Test creating a cache with multiple keys."""
        cache = Cache('test_collection', ('name', 'id'))
        assert cache.keys == ('name', 'id')


class TestCacheReload:
    """Test Cache reload functionality."""
    
    @patch('server.controllers.cache.dbc.read')
    def test_reload_empty(self, mock_read):
        """Test reloading with no records."""
        mock_read.return_value = []
        cache = Cache('test_collection', ('name',))
        cache.reload()
        
        assert cache.data == {}
        mock_read.assert_called_once_with('test_collection', no_id=False)
    
    @patch('server.controllers.cache.dbc.read')
    def test_reload_single_key(self, mock_read):
        """Test reloading with single key."""
        mock_read.return_value = [
            {'_id': '1', 'name': 'test1', 'value': 100},
            {'_id': '2', 'name': 'test2', 'value': 200}
        ]
        cache = Cache('test_collection', ('name',))
        cache.reload()
        
        assert ('test1',) in cache.data
        assert ('test2',) in cache.data
        assert cache.data[('test1',)]['value'] == 100
        assert cache.data[('test2',)]['value'] == 200
    
    @patch('server.controllers.cache.dbc.read')
    def test_reload_multiple_keys(self, mock_read):
        """Test reloading with multiple keys."""
        mock_read.return_value = [
            {'_id': '1', 'name': 'test1', 'type': 'A', 'value': 100},
            {'_id': '2', 'name': 'test1', 'type': 'B', 'value': 200},
            {'_id': '3', 'name': 'test2', 'type': 'A', 'value': 300}
        ]
        cache = Cache('test_collection', ('name', 'type'))
        cache.reload()
        
        assert ('test1', 'A') in cache.data
        assert ('test1', 'B') in cache.data
        assert ('test2', 'A') in cache.data
        assert cache.data[('test1', 'A')]['value'] == 100
        assert cache.data[('test1', 'B')]['value'] == 200
    
    @patch('server.controllers.cache.dbc.read')
    def test_reload_missing_key_field(self, mock_read):
        """Test reloading when a record is missing a key field."""
        mock_read.return_value = [
            {'_id': '1', 'name': 'test1', 'value': 100},
            {'_id': '2', 'value': 200}  # missing 'name' field
        ]
        cache = Cache('test_collection', ('name',))
        cache.reload()
        
        # Record with missing key should have None in tuple
        assert ('test1',) in cache.data
        assert (None,) in cache.data
    
    @patch('server.controllers.cache.dbc.read')
    def test_reload_replaces_existing_data(self, mock_read):
        """Test that reload replaces existing cache data."""
        # First load
        mock_read.return_value = [
            {'_id': '1', 'name': 'test1', 'value': 100}
        ]
        cache = Cache('test_collection', ('name',))
        cache.reload()
        assert ('test1',) in cache.data
        
        # Second load with different data
        mock_read.return_value = [
            {'_id': '2', 'name': 'test2', 'value': 200}
        ]
        cache.reload()
        assert ('test1',) not in cache.data
        assert ('test2',) in cache.data


class TestCacheRead:
    """Test Cache read functionality."""
    
    @patch('server.controllers.cache.dbc.read')
    def test_read_lazy_load(self, mock_read):
        """Test that read() lazy loads data on first call."""
        mock_read.return_value = [
            {'_id': '1', 'name': 'test1', 'value': 100}
        ]
        cache = Cache('test_collection', ('name',))
        
        # Data should be None initially
        assert cache.data is None
        
        # First read should trigger reload
        result = cache.read()
        assert mock_read.call_count == 1
        assert ('test1',) in result
    
    @patch('server.controllers.cache.dbc.read')
    def test_read_no_duplicate_load(self, mock_read):
        """Test that read() doesn't reload if data exists."""
        mock_read.return_value = [
            {'_id': '1', 'name': 'test1', 'value': 100}
        ]
        cache = Cache('test_collection', ('name',))
        
        # First read
        cache.read()
        assert mock_read.call_count == 1
        
        # Second read should not call reload
        cache.read()
        assert mock_read.call_count == 1  # Still 1
    
    @patch('server.controllers.cache.dbc.read')
    def test_read_after_explicit_reload(self, mock_read):
        """Test read after explicit reload."""
        mock_read.return_value = [
            {'_id': '1', 'name': 'test1', 'value': 100}
        ]
        cache = Cache('test_collection', ('name',))
        
        # First read
        cache.read()
        
        # Explicit reload
        cache.reload()
        assert mock_read.call_count == 2
        
        # Read should use reloaded data
        result = cache.read()
        assert mock_read.call_count == 2  # No additional call


class TestCacheIntegration:
    """Integration tests for Cache class."""
    
    @patch('server.controllers.cache.dbc.read')
    def test_typical_usage_pattern(self, mock_read):
        """Test a typical usage pattern: read, modify, reload, read."""
        initial_data = [
            {'_id': '1', 'name': 'state1', 'nation': 'USA'}
        ]
        updated_data = [
            {'_id': '1', 'name': 'state1', 'nation': 'USA'},
            {'_id': '2', 'name': 'state2', 'nation': 'Canada'}
        ]
        
        mock_read.return_value = initial_data
        cache = Cache('states', ('name',))
        
        # Initial read
        states = cache.read()
        assert len(states) == 1
        assert ('state1',) in states
        
        # Simulate external modification, then reload
        mock_read.return_value = updated_data
        cache.reload()
        
        # Read again
        states = cache.read()
        assert len(states) == 2
        assert ('state1',) in states
        assert ('state2',) in states

