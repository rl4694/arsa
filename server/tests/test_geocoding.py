import pytest
from unittest.mock import patch, MagicMock
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

import server.etl.geocoding as geo


@pytest.fixture(autouse=True)
def patch_dependencies():
    with patch('server.etl.geocoding.geocode') as mock_geocode:
        yield


class TestReverseGeocode:
    """Test the reverse_geocode function."""
    
    @patch('server.etl.geocoding.reverse')
    def test_valid_coordinates(self, mock_reverse):
        """Test reverse geocoding with valid coordinates."""
        # Mock the location response
        mock_location = MagicMock()
        mock_location.address = "New York City Hall, 260, Broadway, Manhattan"
        mock_location.raw = {
            'address': {
                'city': 'New York',
                'state': 'New York',
                'country': 'United States'
                'country_code': 'us'
            }
        }
        mock_reverse.return_value = mock_location
        
        result = geo.reverse_geocode(40.7128, -74.0060)
        
        assert result['city'] == 'New York'
        assert result['state'] == 'New York'
        assert result['country'] == 'United States'
        assert result['latitude'] == 40.7128
        assert result['longitude'] == -74.0060
        assert 'display_name' in result
    
    @patch('server.etl.geocoding.reverse')
    def test_location_with_province_instead_of_state(self, mock_reverse):
        """Test that province is used when state is not available."""
        mock_location = MagicMock()
        mock_location.address = "Toronto, Ontario, Canada"
        mock_location.raw = {
            'address': {
                'city': 'Toronto',
                'province': 'Ontario',
                'country': 'Canada'
                'country_code': 'ca'
            }
        }
        mock_reverse.return_value = mock_location
        
        result = geo.reverse_geocode(43.65, -79.38)
        
        assert result['city'] == 'Toronto'
        assert result['state'] == 'Ontario'
        assert result['country'] == 'Canada'
    
    @patch('server.etl.geocoding.reverse')
    def test_location_not_found(self, mock_reverse):
        """Test when coordinates don't map to any location."""
        mock_reverse.return_value = None
        
        result = geo.reverse_geocode(0.0, 0.0)
        
        assert result['city'] is None
        assert result['state'] is None
        assert result['country'] is None
        assert result['display_name'] == 'Location not found'
    
    def test_invalid_latitude_too_high(self):
        """Test that latitude > 90 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            geo.reverse_geocode(91.0, 0.0)
        assert "Latitude must be between -90 and 90" in str(exc_info.value)
    
    def test_invalid_latitude_too_low(self):
        """Test that latitude < -90 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            geo.reverse_geocode(-91.0, 0.0)
        assert "Latitude must be between -90 and 90" in str(exc_info.value)
    
    def test_invalid_longitude_too_high(self):
        """Test that longitude > 180 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            geo.reverse_geocode(0.0, 181.0)
        assert "Longitude must be between -180 and 180" in str(exc_info.value)
    
    def test_invalid_longitude_too_low(self):
        """Test that longitude < -180 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            geo.reverse_geocode(0.0, -181.0)
        assert "Longitude must be between -180 and 180" in str(exc_info.value)
    
    def test_non_numeric_latitude(self):
        """Test that non-numeric latitude raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            geo.reverse_geocode("not a number", 0.0)
        assert "must be numbers" in str(exc_info.value)
    
    def test_non_numeric_longitude(self):
        """Test that non-numeric longitude raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            geo.reverse_geocode(0.0, "not a number")
        assert "must be numbers" in str(exc_info.value)
    
    @patch('server.etl.geocoding.reverse')
    def test_geocoder_timeout(self, mock_reverse):
        """Test handling of geocoder timeout."""
        mock_reverse.side_effect = GeocoderTimedOut()
        
        with pytest.raises(GeocoderTimedOut):
            geo.reverse_geocode(40.7128, -74.0060)
    
    @patch('server.etl.geocoding.reverse')
    def test_geocoder_service_error(self, mock_reverse):
        """Test handling of geocoder service error."""
        mock_reverse.side_effect = GeocoderServiceError("Service unavailable")
        
        with pytest.raises(GeocoderServiceError):
            geo.reverse_geocode(40.7128, -74.0060)


class TestGeocodeEndpoint:
    """Test the /geocode API endpoint."""
    
    def setup_method(self):
        """Set up test client before each test."""
        from server.endpoints import app
        self.client = app.test_client()
    
    @patch('server.etl.geocoding.reverse_geocode')
    def test_get_with_valid_params(self, mock_reverse_geocode):
        """Test GET request with valid lat/lon parameters."""
        mock_reverse_geocode.return_value = {
            'city': 'New York',
            'state': 'New York',
            'country': 'United States',
            'country_code': 'us',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'display_name': 'New York, NY, USA'
        }
        
        response = self.client.get('/geocode/?lat=40.7128&lon=-74.0060')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['city'] == 'New York'
        assert data['state'] == 'New York'
        assert data['country'] == 'United States'
    
    def test_get_missing_lat_param(self):
        """Test GET request missing lat parameter."""
        response = self.client.get('/geocode/?lon=-74.0060')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'lat' in data['message'].lower()
    
    def test_get_missing_lon_param(self):
        """Test GET request missing lon parameter."""
        response = self.client.get('/geocode/?lat=40.7128')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'lon' in data['message'].lower()
    
    def test_get_missing_both_params(self):
        """Test GET request missing both parameters."""
        response = self.client.get('/geocode/')
        
        assert response.status_code == 400
    
    def test_get_invalid_lat_format(self):
        """Test GET request with non-numeric latitude."""
        response = self.client.get('/geocode/?lat=abc&lon=-74.0060')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'valid numbers' in data['message'].lower()
    
    def test_get_invalid_lon_format(self):
        """Test GET request with non-numeric longitude."""
        response = self.client.get('/geocode/?lat=40.7128&lon=xyz')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'valid numbers' in data['message'].lower()
    
    @patch('server.etl.geocoding.reverse_geocode')
    def test_get_out_of_range_coordinates(self, mock_reverse_geocode):
        """Test GET request with out-of-range coordinates."""
        mock_reverse_geocode.side_effect = ValueError("Latitude must be between -90 and 90")
        
        response = self.client.get('/geocode/?lat=100&lon=0')
        
        assert response.status_code == 400
    
    @patch('server.etl.geocoding.reverse_geocode')
    def test_get_service_timeout(self, mock_reverse_geocode):
        """Test handling when geocoding service times out."""
        mock_reverse_geocode.side_effect = GeocoderTimedOut()
        
        response = self.client.get('/geocode/?lat=40.7128&lon=-74.0060')
        
        assert response.status_code == 503
    
    @patch('server.etl.geocoding.reverse_geocode')
    def test_get_service_error(self, mock_reverse_geocode):
        """Test handling when geocoding service fails."""
        mock_reverse_geocode.side_effect = GeocoderServiceError("Service error")
        
        response = self.client.get('/geocode/?lat=40.7128&lon=-74.0060')
        
        assert response.status_code == 503
    
    @pytest.mark.skip(reason="Future feature: batch geocoding not yet implemented")
    def test_batch_geocode_multiple_locations(self):
        """Test batch geocoding of multiple coordinate pairs (future feature)."""
        # This test is skipped because batch geocoding is planned for v2.0
        response = self.client.post('/geocode/batch', json={
            'locations': [
                {'lat': 40.7128, 'lon': -74.0060},
                {'lat': 34.0522, 'lon': -118.2437}
            ]
        })
        assert response.status_code == 200
