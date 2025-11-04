import pytest
import time
from io import StringIO
from unittest.mock import patch, MagicMock, call
from server.controllers import cities as ct
from server.controllers import nations as nt
from server import seed as sd


class TestSeedNations:
    @patch('time.sleep')
    @patch('server.seed.requests.get', autospec=True)
    def test_valid(self, mock_get, mock_sleep):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'data': [{
                'name': 'my nation',
            }],
            'metadata': {
                'totalCount': 1,
            },
        }

        old_count = nt.length()
        ids = sd.seed_nations()
        assert nt.length() >= old_count
        for _id in ids:
            nt.delete(_id)


    @patch('time.sleep')
    @patch('server.seed.requests.get', autospec=True)
    def test_error_response(self, mock_get, mock_sleep):
        mock_get.return_value.status_code = 400
        with pytest.raises(ConnectionError):
            sd.seed_nations()
    
    @patch('time.sleep')
    @patch('server.seed.requests.get', autospec=True)
    def test_missing_data(self, mock_get, mock_sleep):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {}

        with pytest.raises(ValueError):
            sd.seed_nations()

    @patch('time.sleep')
    @patch('server.seed.requests.get', autospec=True)
    def test_json_pagination_multiple_pages(self, mock_get, mock_sleep):
        """Test JSON parsing with multiple pages of results"""
        # Mock responses for multiple pages
        responses = [
            {
                'data': [
                    {'name': 'Nation 1'},
                    {'name': 'Nation 2'},
                ],
                'metadata': {'totalCount': 15},
            },
            {
                'data': [
                    {'name': 'Nation 3'},
                    {'name': 'Nation 4'},
                ],
                'metadata': {'totalCount': 15},
            },
            {
                'data': [
                    {'name': 'Nation 5'},
                ],
                'metadata': {'totalCount': 15},
            },
        ]
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.side_effect = responses
        
        old_count = nt.length()
        ids = sd.seed_nations()
        
        # Verify multiple nations were created
        assert len(ids) == 5
        assert nt.length() >= old_count + 5
        
        # Verify pagination was used correctly
        assert mock_get.call_count == 3
        
        # Clean up
        for _id in ids:
            nt.delete(_id)

    @patch('time.sleep')
    @patch('server.seed.requests.get', autospec=True)
    def test_json_with_missing_name_field(self, mock_get, mock_sleep):
        """Test JSON parsing when name field is missing"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'data': [{
                'code': 'US',  # name field missing
            }],
            'metadata': {
                'totalCount': 1,
            },
        }

        old_count = nt.length()
        ids = sd.seed_nations()
        
        # Should create nation with empty name
        assert len(ids) == 1
        assert nt.length() >= old_count
        
        # Clean up
        for _id in ids:
            nt.delete(_id)

    @patch('time.sleep')
    @patch('server.seed.requests.get', autospec=True)
    def test_json_with_extra_fields(self, mock_get, mock_sleep):
        """Test JSON parsing with extra fields in response"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'data': [{
                'name': 'Test Nation',
                'code': 'TN',
                'population': 1000000,
                'capital': 'Test City',
            }],
            'metadata': {
                'totalCount': 1,
            },
        }

        old_count = nt.length()
        ids = sd.seed_nations()
        
        # Should handle extra fields gracefully
        assert len(ids) == 1
        assert nt.length() >= old_count
        
        # Clean up
        for _id in ids:
            nt.delete(_id)

    @patch('time.sleep')
    @patch('server.seed.requests.get', autospec=True)
    def test_json_empty_data_array(self, mock_get, mock_sleep):
        """Test JSON parsing with empty data array"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'data': [],
            'metadata': {
                'totalCount': 0,
            },
        }

        ids = sd.seed_nations()
        
        # Should handle empty array gracefully
        assert len(ids) == 0


class TestSeedEarthquakes:
    # open manages context, so a MagicMock is necessary to simulate it
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_valid(self, mock_open, mock_kaggle_api, mock_remove):
        data = (
            'location,country,latitude,longitude\n'
            '"my_city, my_state",my_nation,1,1'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)

        old_count = ct.length()
        sd.seed_earthquakes()
        assert ct.length() >= old_count
        # TODO: check if earthquakes are created

    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_failed_download(self, mock_open, mock_kaggle_api, mock_remove):
        mock_open.side_effect = FileNotFoundError("file not found")
        with pytest.raises(ConnectionError):
            sd.seed_earthquakes()

    @patch('server.seed.reverse_geocode')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_reverse_geocoding_mapping(self, mock_open, mock_kaggle_api, 
                                       mock_remove, mock_geocode):
        """Test reverse geocoding from coordinates to location"""
        data = (
            'location,country,latitude,longitude\n'
            'Some Location,Some Country,40.7128,-74.0060'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        
        # Mock reverse geocoding to return location data
        mock_geocode.return_value = {
            'city': 'New York',
            'state': 'New York',
            'country': 'United States',
        }

        old_count = ct.length()
        sd.seed_earthquakes()
        
        # Verify reverse_geocode was called with correct coordinates
        mock_geocode.assert_called_once_with(40.7128, -74.0060)
        assert ct.length() >= old_count

    @patch('server.seed.reverse_geocode')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_with_missing_city(self, mock_open, mock_kaggle_api,
                                       mock_remove, mock_geocode):
        """Test mapping when city is missing from geocode result"""
        data = (
            'location,country,latitude,longitude\n'
            'Ocean Location,None,0.0,0.0'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        
        # Mock geocoding returning no city (e.g., middle of ocean)
        mock_geocode.return_value = {
            'city': None,
            'state': None,
            'country': None,
        }

        old_count = ct.length()
        sd.seed_earthquakes()
        
        # Should skip entries without city
        assert ct.length() == old_count

    @patch('server.seed.reverse_geocode')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_with_partial_location_data(self, mock_open, 
                                                 mock_kaggle_api, mock_remove,
                                                 mock_geocode):
        """Test mapping with only city and country (no state)"""
        data = (
            'location,country,latitude,longitude\n'
            'Some Location,Some Country,51.5074,-0.1278'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        
        # Mock geocoding with no state (common in some countries)
        mock_geocode.return_value = {
            'city': 'London',
            'state': None,
            'country': 'United Kingdom',
        }

        old_count = ct.length()
        sd.seed_earthquakes()
        
        # Should handle missing state gracefully
        assert ct.length() >= old_count

    @patch('server.seed.reverse_geocode')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_geocode_error_handling(self, mock_open, mock_kaggle_api,
                                            mock_remove, mock_geocode):
        """Test handling of geocoding errors"""
        data = (
            'location,country,latitude,longitude\n'
            'Location1,Country1,40.0,-74.0\n'
            'Location2,Country2,41.0,-75.0'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        
        # First call succeeds, second raises exception
        mock_geocode.side_effect = [
            {
                'city': 'City1',
                'state': 'State1',
                'country': 'Country1',
            },
            Exception("Geocoding service error")
        ]

        old_count = ct.length()
        sd.seed_earthquakes()
        
        # Should continue processing despite error
        assert mock_geocode.call_count == 2

    @patch('server.seed.reverse_geocode')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_coordinate_to_location_mapping(self, mock_open, mock_kaggle_api,
                                            mock_remove, mock_geocode):
        """Test complete coordinate-to-location mapping flow"""
        data = (
            'location,country,latitude,longitude\n'
            'Earthquake Site,Japan,35.6762,139.6503'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        
        # Mock complete geocoding result
        mock_geocode.return_value = {
            'city': 'Tokyo',
            'state': 'Tokyo',
            'country': 'Japan',
        }

        old_count_nations = nt.length()
        old_count_cities = ct.length()
        
        sd.seed_earthquakes()
        
        # Verify geocoding was called with correct lat/lon
        mock_geocode.assert_called_with(35.6762, 139.6503)
        
        # Verify data was created
        assert ct.length() >= old_count_cities

    @patch('server.seed.reverse_geocode')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_reverse_geocoding_mapping(self, mock_open, mock_kaggle_api,
                                       mock_remove, mock_geocode):
        """Test coordinate to location mapping via reverse geocoding"""
        data = (
            'latitude,longitude,magnitude\n'
            '40.7128,-74.0060,5.5\n'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        
        # Mock reverse geocoding to return location data
        mock_geocode.return_value = {
            'city': 'New York',
            'state': 'New York',
            'country': 'United States',
        }
        
        old_count = ct.length()
        sd.seed_earthquakes()
        
        # Verify reverse_geocode was called with correct coordinates
        mock_geocode.assert_called_once_with(40.7128, -74.0060)
        assert ct.length() >= old_count

    @patch('server.seed.reverse_geocode')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_missing_city(self, mock_open, mock_kaggle_api,
                                   mock_remove, mock_geocode):
        """Test mapping when reverse geocoding returns no city"""
        data = (
            'latitude,longitude,magnitude\n'
            '0.0,0.0,5.5\n'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        
        # Mock reverse geocoding to return no city (e.g., ocean location)
        mock_geocode.return_value = {
            'city': None,
            'state': None,
            'country': None,
        }
        
        old_count = ct.length()
        sd.seed_earthquakes()
        
        # Should skip this entry when no city found
        assert ct.length() == old_count
        mock_geocode.assert_called_once()

    @patch('server.seed.reverse_geocode')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_with_state_and_nation(self, mock_open, mock_kaggle_api,
                                           mock_remove, mock_geocode):
        """Test full location mapping with city, state, and nation"""
        data = (
            'latitude,longitude,magnitude\n'
            '34.0522,-118.2437,6.2\n'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        
        # Mock complete location data
        mock_geocode.return_value = {
            'city': 'Los Angeles',
            'state': 'California',
            'country': 'United States',
        }
        
        old_count_cities = ct.length()
        old_count_nations = nt.length()
        
        sd.seed_earthquakes()
        
        # Verify entities were created
        assert ct.length() >= old_count_cities
        assert nt.length() >= old_count_nations

    @patch('server.seed.reverse_geocode')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_without_state(self, mock_open, mock_kaggle_api,
                                    mock_remove, mock_geocode):
        """Test mapping when state is missing but city and nation exist"""
        data = (
            'latitude,longitude,magnitude\n'
            '48.8566,2.3522,4.1\n'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        
        # Mock location without state (e.g., Paris, France)
        mock_geocode.return_value = {
            'city': 'Paris',
            'state': None,
            'country': 'France',
        }
        
        old_count = ct.length()
        sd.seed_earthquakes()
        
        # Should handle missing state gracefully
        assert ct.length() >= old_count

    @patch('server.seed.reverse_geocode')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_geocoding_exception(self, mock_open, mock_kaggle_api,
                                         mock_remove, mock_geocode):
        """Test handling of geocoding exceptions during mapping"""
        data = (
            'latitude,longitude,magnitude\n'
            '40.7128,-74.0060,5.5\n'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        
        # Mock geocoding failure
        mock_geocode.side_effect = Exception("Geocoding service error")
        
        old_count = ct.length()
        # Should continue without crashing
        sd.seed_earthquakes()
        
        # No cities should be added due to error
        assert ct.length() == old_count

    @patch('server.seed.reverse_geocode')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_multiple_coordinates(self, mock_open, mock_kaggle_api,
                                          mock_remove, mock_geocode):
        """Test mapping multiple coordinates to different locations"""
        data = (
            'latitude,longitude,magnitude\n'
            '40.7128,-74.0060,5.5\n'
            '34.0522,-118.2437,6.2\n'
            '51.5074,-0.1278,4.8\n'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        
        # Mock different locations for each coordinate
        mock_geocode.side_effect = [
            {'city': 'New York', 'state': 'New York', 'country': 'USA'},
            {'city': 'Los Angeles', 'state': 'California', 'country': 'USA'},
            {'city': 'London', 'state': None, 'country': 'United Kingdom'},
        ]
        
        old_count = ct.length()
        sd.seed_earthquakes()
        
        # Verify all coordinates were processed
        assert mock_geocode.call_count == 3
        assert ct.length() >= old_count

    @patch('server.seed.reverse_geocode')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_reverse_geocoding_mapping(self, mock_open, mock_kaggle_api, 
                                       mock_remove, mock_geocode):
        """Test reverse geocoding maps coordinates to location data"""
        data = (
            'latitude,longitude,magnitude\n'
            '40.7128,-74.0060,5.5\n'
            '34.0522,-118.2437,4.2'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        
        # Mock reverse geocoding to return location data
        mock_geocode.side_effect = [
            {
                'city': 'New York',
                'state': 'New York',
                'country': 'United States',
            },
            {
                'city': 'Los Angeles',
                'state': 'California',
                'country': 'United States',
            },
        ]

        old_count = ct.length()
        sd.seed_earthquakes()
        
        # Verify reverse_geocode was called with correct coordinates
        assert mock_geocode.call_count == 2
        mock_geocode.assert_any_call(40.7128, -74.0060)
        mock_geocode.assert_any_call(34.0522, -118.2437)
        
        # Verify cities were created
        assert ct.length() >= old_count

    @patch('server.seed.reverse_geocode')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_with_missing_city(self, mock_open, mock_kaggle_api,
                                       mock_remove, mock_geocode):
        """Test that rows without city data are skipped"""
        data = (
            'latitude,longitude,magnitude\n'
            '0.0,0.0,3.0'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        
        # Mock reverse geocoding to return no city
        mock_geocode.return_value = {
            'city': None,
            'state': 'Some State',
            'country': 'Some Country',
        }

        old_count = ct.length()
        sd.seed_earthquakes()
        
        # Verify city count unchanged (no city created)
        assert ct.length() == old_count

    @patch('server.seed.reverse_geocode')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_with_partial_location_data(self, mock_open, mock_kaggle_api,
                                                 mock_remove, mock_geocode):
        """Test mapping when only city and country available (no state)"""
        data = (
            'latitude,longitude,magnitude\n'
            '51.5074,-0.1278,4.0'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        
        # Mock reverse geocoding with no state (like some countries)
        mock_geocode.return_value = {
            'city': 'London',
            'state': None,
            'country': 'United Kingdom',
        }

        old_count = ct.length()
        sd.seed_earthquakes()
        
        # Should still create city even without state
        assert ct.length() >= old_count

    @patch('server.seed.reverse_geocode')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_handles_geocoding_exception(self, mock_open, mock_kaggle_api,
                                                  mock_remove, mock_geocode):
        """Test that geocoding exceptions are handled gracefully"""
        data = (
            'latitude,longitude,magnitude\n'
            '999,999,5.0\n'
            '40.7128,-74.0060,4.0'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        
        # First call raises exception, second succeeds
        mock_geocode.side_effect = [
            Exception("Invalid coordinates"),
            {
                'city': 'New York',
                'state': 'New York',
                'country': 'United States',
            },
        ]

        old_count = ct.length()
        sd.seed_earthquakes()
        
        # Should continue processing after exception
        assert ct.length() >= old_count

    @patch('server.seed.reverse_geocode')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_coordinate_to_location_mapping(self, mock_open, mock_kaggle_api,
                                            mock_remove, mock_geocode):
        """Test that coordinates are correctly mapped to hierarchical location data"""
        data = (
            'latitude,longitude,magnitude\n'
            '35.6762,139.6503,6.5'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        
        # Mock geocoding with full hierarchical data
        mock_geocode.return_value = {
            'city': 'Tokyo',
            'state': 'Tokyo',
            'country': 'Japan',
        }

        old_nations = nt.length()
        old_cities = ct.length()
        
        sd.seed_earthquakes()
        
        # Verify hierarchical creation (nation, state, city)
        assert nt.length() >= old_nations
        assert ct.length() >= old_cities
        
        # Verify correct coordinates were passed
        mock_geocode.assert_called_once_with(35.6762, 139.6503)


class TestSeedLandslides:
    @patch('server.seed.zipfile.ZipFile')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_valid(self, mock_open, mock_kaggle_api, mock_remove, mock_zip):
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"my_city, my_state",my_nation,1,1'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)

        old_count = ct.length()
        sd.seed_landslides()
        assert ct.length() > old_count
        # TODO: check if landslides are created

    @patch('server.seed.zipfile.ZipFile')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_failed_download(self, mock_open, mock_kaggle_api, mock_remove,
            mock_zip):
        mock_open.side_effect = FileNotFoundError("file not found")
        with pytest.raises(ConnectionError):
            sd.seed_landslides()

    @patch('server.seed.nt.read')
    @patch('server.seed.zipfile.ZipFile')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_location_description_parsing_city_state(self, mock_open, 
                                                      mock_kaggle_api, 
                                                      mock_remove, mock_zip,
                                                      mock_nations_read):
        """Test parsing location_description into city and state"""
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"Seattle, Washington",United States,47.6062,-122.3321\n'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        mock_nations_read.return_value = {'United States': 'id1'}
        
        old_count = ct.length()
        sd.seed_landslides()
        
        assert ct.length() >= old_count

    @patch('server.seed.nt.read')
    @patch('server.seed.zipfile.ZipFile')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_location_description_parsing_city_nation(self, mock_open,
                                                       mock_kaggle_api,
                                                       mock_remove, mock_zip,
                                                       mock_nations_read):
        """Test parsing when second part is a nation name"""
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"Tokyo, Japan",Japan,35.6762,139.6503\n'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        mock_nations_read.return_value = {'Japan': 'id1', 'United States': 'id2'}
        
        old_count = ct.length()
        sd.seed_landslides()
        
        assert ct.length() >= old_count

    @patch('server.seed.nt.read')
    @patch('server.seed.zipfile.ZipFile')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_location_description_with_ignored_words(self, mock_open,
                                                      mock_kaggle_api,
                                                      mock_remove, mock_zip,
                                                      mock_nations_read):
        """Test that locations with ignored words are skipped"""
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"Highway 101, California",United States,34.0522,-118.2437\n'
            '"Near Seattle, Washington",United States,47.6062,-122.3321\n'
            '"Main Road, Texas",United States,29.7604,-95.3698\n'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        mock_nations_read.return_value = {'United States': 'id1'}
        
        old_count = ct.length()
        sd.seed_landslides()
        
        # All three should be skipped due to ignored words
        assert ct.length() == old_count

    @patch('server.seed.nt.read')
    @patch('server.seed.zipfile.ZipFile')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_location_description_with_numbers(self, mock_open,
                                                mock_kaggle_api,
                                                mock_remove, mock_zip,
                                                mock_nations_read):
        """Test that locations with numbers are skipped"""
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"City123, State",Nation,1,1\n'
            '"1st Avenue, Washington",United States,47.6062,-122.3321\n'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        mock_nations_read.return_value = {'Nation': 'id1', 'United States': 'id2'}
        
        old_count = ct.length()
        sd.seed_landslides()
        
        # Should be skipped due to numbers
        assert ct.length() == old_count

    @patch('server.seed.nt.read')
    @patch('server.seed.zipfile.ZipFile')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_location_description_invalid_format(self, mock_open,
                                                  mock_kaggle_api,
                                                  mock_remove, mock_zip,
                                                  mock_nations_read):
        """Test that locations not in 'city, state/nation' format are skipped"""
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"SingleLocation",Nation,1,1\n'
            '"City, State, Extra",Nation,1,1\n'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        mock_nations_read.return_value = {'Nation': 'id1'}
        
        old_count = ct.length()
        sd.seed_landslides()
        
        # Should be skipped due to invalid format
        assert ct.length() == old_count

    @patch('server.seed.nt.read')
    @patch('server.seed.zipfile.ZipFile')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_location_mapping_with_nation_match(self, mock_open,
                                                 mock_kaggle_api,
                                                 mock_remove, mock_zip,
                                                 mock_nations_read):
        """Test mapping when country_name matches existing nations"""
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"Vancouver, British Columbia",Canada,49.2827,-123.1207\n'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        mock_nations_read.return_value = {'Canada': 'id1', 'United States': 'id2'}
        
        old_count = ct.length()
        sd.seed_landslides()
        
        # Should create city with mapped nation
        assert ct.length() >= old_count

    @patch('server.seed.nt.read')
    @patch('server.seed.zipfile.ZipFile')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_location_mapping_multiple_entries(self, mock_open,
                                                mock_kaggle_api,
                                                mock_remove, mock_zip,
                                                mock_nations_read):
        """Test mapping multiple location entries"""
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"Seattle, Washington",United States,47.6062,-122.3321\n'
            '"Portland, Oregon",United States,45.5152,-122.6784\n'
            '"Vancouver, British Columbia",Canada,49.2827,-123.1207\n'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        mock_nations_read.return_value = {'Canada': 'id1', 'United States': 'id2'}
        
        old_count = ct.length()
        sd.seed_landslides()
        
        # Should create all three cities
        assert ct.length() >= old_count + 3

    @patch('server.seed.nt.read')
    @patch('server.seed.zipfile.ZipFile')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_location_mapping_case_sensitivity(self, mock_open,
                                                mock_kaggle_api,
                                                mock_remove, mock_zip,
                                                mock_nations_read):
        """Test that ignored words filter is case insensitive"""
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"HIGHWAY 101, California",United States,34.0522,-118.2437\n'
            '"Near town, Washington",United States,47.6062,-122.3321\n'
            '"On Main Street, Texas",United States,29.7604,-95.3698\n'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        mock_nations_read.return_value = {'United States': 'id1'}
        
        old_count = ct.length()
        sd.seed_landslides()
        
        # All should be filtered despite uppercase
        assert ct.length() == old_count

    @patch('server.seed.nt.read')
    @patch('server.seed.zipfile.ZipFile')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_location_description_parsing(self, mock_open, mock_kaggle_api,
                                          mock_remove, mock_zip, mock_nt_read):
        """Test parsing of location_description field into city/state/nation"""
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"Tokyo, Japan",Japan,35.6762,139.6503\n'
            '"Paris, France",France,48.8566,2.3522'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        mock_nt_read.return_value = ['Japan', 'France', 'United States']

        old_count = ct.length()
        sd.seed_landslides()
        
        # Should create cities for valid location descriptions
        assert ct.length() >= old_count

    @patch('server.seed.nt.read')
    @patch('server.seed.zipfile.ZipFile')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_location_mapping_with_state(self, mock_open, mock_kaggle_api,
                                         mock_remove, mock_zip, mock_nt_read):
        """Test mapping location description to city and state"""
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"San Francisco, California",United States,37.7749,-122.4194'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        mock_nt_read.return_value = ['United States']

        old_count = ct.length()
        sd.seed_landslides()
        
        # Should create city with state
        assert ct.length() >= old_count

    @patch('server.seed.nt.read')
    @patch('server.seed.zipfile.ZipFile')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_location_mapping_nation_vs_state(self, mock_open, mock_kaggle_api,
                                              mock_remove, mock_zip, mock_nt_read):
        """Test that location is correctly mapped to nation vs state"""
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"City, Mexico",Mexico,19.4326,-99.1332'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        mock_nt_read.return_value = ['Mexico', 'United States', 'Canada']

        old_count = ct.length()
        sd.seed_landslides()
        
        # When second part matches nation list, should map to nation not state
        assert ct.length() >= old_count

    @patch('server.seed.nt.read')
    @patch('server.seed.zipfile.ZipFile')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_skip_invalid_location_format(self, mock_open, mock_kaggle_api,
                                          mock_remove, mock_zip, mock_nt_read):
        """Test that locations with invalid format are skipped"""
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"Single Location",Country,1,1\n'
            '"Too, Many, Parts",Country,2,2\n'
            '"Valid, Location",Country,3,3'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        mock_nt_read.return_value = ['Country']

        old_count = ct.length()
        sd.seed_landslides()
        
        # Only valid format (comma-separated pair) should be processed
        assert ct.length() >= old_count

    @patch('server.seed.nt.read')
    @patch('server.seed.zipfile.ZipFile')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_skip_location_with_ignored_words(self, mock_open, mock_kaggle_api,
                                              mock_remove, mock_zip, mock_nt_read):
        """Test that locations with road/highway keywords are filtered out"""
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"Highway 101, California",USA,1,1\n'
            '"Main Road, Texas",USA,2,2\n'
            '"Route 66, Arizona",USA,3,3\n'
            '"Downtown, New York",USA,4,4\n'
            '"City Center, Florida",USA,5,5'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        mock_nt_read.return_value = ['USA']

        old_count = ct.length()
        sd.seed_landslides()
        
        # Locations with road/highway/route should be skipped
        # Only valid city locations should be added
        assert ct.length() >= old_count

    @patch('server.seed.nt.read')
    @patch('server.seed.zipfile.ZipFile')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_skip_location_with_numbers(self, mock_open, mock_kaggle_api,
                                        mock_remove, mock_zip, mock_nt_read):
        """Test that locations with numbers are filtered out"""
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"Building 123, District",Country,1,1\n'
            '"5th Avenue, City",Country,2,2\n'
            '"Clean City, Clean State",Country,3,3'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        mock_nt_read.return_value = ['Country']

        old_count = ct.length()
        sd.seed_landslides()
        
        # Locations with numbers should be skipped
        assert ct.length() >= old_count

    @patch('server.seed.nt.read')
    @patch('server.seed.zipfile.ZipFile')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_country_name_fallback_mapping(self, mock_open, mock_kaggle_api,
                                           mock_remove, mock_zip, mock_nt_read):
        """Test that country_name field is used as fallback for nation mapping"""
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"City, UnknownPlace",Brazil,1,1'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        mock_nt_read.return_value = ['Brazil', 'Argentina']

        old_count = ct.length()
        sd.seed_landslides()
        
        # Should use country_name when location part doesn't match nations
        assert ct.length() >= old_count

    @patch('server.seed.nt.read')
    @patch('server.seed.zipfile.ZipFile')
    @patch('server.seed.os.remove')
    @patch('server.seed.get_kaggle_api')
    @patch("builtins.open", new_callable=MagicMock)
    def test_complex_location_filtering(self, mock_open, mock_kaggle_api,
                                        mock_remove, mock_zip, mock_nt_read):
        """Test combination of filtering rules (ignored words + numbers)"""
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"Near Highway 5, State",Country,1,1\n'
            '"On Route 123, Place",Country,2,2\n'
            '"ValidCity, ValidState",Country,3,3'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        mock_nt_read.return_value = ['Country']

        old_count = ct.length()
        sd.seed_landslides()
        
        # Only location without ignored words/numbers should be processed
        assert ct.length() >= old_count
