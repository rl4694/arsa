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
        cache = Cache('test_collection')
        assert cache.collection == 'test_collection'
        assert cache.data is None
    
    def test_invalid_collection_type(self):
        """Test that non-string collection raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            Cache(123)
        assert 'Bad type for collection' in str(exc_info.value)


class TestCacheReload:
    """Test Cache reload functionality."""
    
    @patch('server.controllers.cache.dbc.read')
    def test_reload_empty(self, mock_read):
        """Test reloading with no records."""
        mock_read.return_value = []
        cache = Cache('test_collection',)
        cache.reload()
        
        assert cache.data == {}
        mock_read.assert_called_once_with('test_collection', no_id=False)
    
    @patch('server.controllers.cache.dbc.read')
    def test_reload_basic(self, mock_read):
        """Test basic reloading."""
        mock_read.return_value = [
            {'_id': '1', 'name': 'test1', 'value': 100},
            {'_id': '2', 'name': 'test2', 'value': 200}
        ]
        cache = Cache('test_collection')
        cache.reload()
        
        assert '1' in cache.data
        assert '2' in cache.data
        assert cache.data['1']['value'] == 100
        assert cache.data['2']['value'] == 200

    @patch('server.controllers.cache.dbc.read')
    def test_reload_replaces_existing_data(self, mock_read):
        """Test that reload replaces existing cache data."""
        # First load
        mock_read.return_value = [
            {'_id': '1', 'name': 'test1', 'value': 100}
        ]
        cache = Cache('test_collection')
        cache.reload()
        assert '1' in cache.data
        
        # Second load with different data
        mock_read.return_value = [
            {'_id': '2', 'name': 'test2', 'value': 200}
        ]
        cache.reload()
        assert '1' not in cache.data
        assert '2' in cache.data


class TestCacheRead:
    """Test Cache read functionality."""
    
    @patch('server.controllers.cache.dbc.read')
    def test_read_lazy_load(self, mock_read):
        """Test that read() lazy loads data on first call."""
        mock_read.return_value = [
            {'_id': '1', 'name': 'test1', 'value': 100}
        ]
        cache = Cache('test_collection')
        
        # Data should be None initially
        assert cache.data is None
        
        # First read should trigger reload
        result = cache.read()
        assert mock_read.call_count == 1
        assert '1' in result
    
    @patch('server.controllers.cache.dbc.read')
    def test_read_no_duplicate_load(self, mock_read):
        """Test that read() doesn't reload if data exists."""
        mock_read.return_value = [
            {'_id': '1', 'name': 'test1', 'value': 100}
        ]
        cache = Cache('test_collection')
        
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
        cache = Cache('test_collection')
        
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
        cache = Cache('states')
        
        # Initial read
        states = cache.read()
        assert len(states) == 1
        assert '1' in states
        
        # Simulate external modification, then reload
        mock_read.return_value = updated_data
        cache.reload()
        
        # Read again
        states = cache.read()
        assert len(states) == 2
        assert '1' in states
        assert '2' in states

