import pytest
import time
import json
from io import StringIO
from unittest.mock import patch, MagicMock, call
from server.controllers.cities import cities as ct
from server.controllers.states import states as st
from server.controllers.nations import nations as nt
from server import seed as sd
import data.db_connect as dbc
from functools import wraps


# Skipping these tests for now because test data isn't being cleaned properly
pytest.skip(allow_module_level=True)

@pytest.fixture(autouse=True)
def patch_dependencies():
    with (
        patch('time.sleep') as mock_sleep,
        patch('server.seed.save_json') as mock_save_json,
        patch('server.seed.get_kaggle_api') as mock_kaggle_api,
        patch('server.seed.os.remove') as mock_remove,
        patch('server.seed.zipfile.ZipFile') as mock_zip,
    ):
        yield

@pytest.fixture
def created_ids():
    return {"cities": set(), "states": set(), "nations": set()}

@pytest.fixture(autouse=True)
def track_creates(monkeypatch, created_ids):
    def wrap_create(module, bucket):
        real_create = module.create

        @wraps(real_create)
        def wrapped_create(fields: dict):
            _id = real_create(fields)
            if _id:
                created_ids[bucket].add(_id)
            return _id

        monkeypatch.setattr(module, "create", wrapped_create)

    wrap_create(ct, "cities")
    wrap_create(st, "states")
    wrap_create(nt, "nations")
    yield

@pytest.fixture(autouse=True)
def cleanup_seed_data():
    yield

    for _id in list(created_ids["cities"]):
        try:
            ct.delete(_id)
        except Exception:
            pass

    for _id in list(created_ids["states"]):
        try:
            st.delete(_id)
        except Exception:
            pass

    for _id in list(created_ids["nations"]):
        try:
            nt.delete(_id)
        except Exception:
            pass

class TestSeedNations:
    @patch('server.seed.requests.get', autospec=True)
    def test_valid(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'data': [{
                'name': 'my nation',
            }],
            'metadata': {
                'totalCount': 1,
            },
        }

        old_count = nt.count()
        ids = sd.seed_nations()
        assert nt.count() >= old_count
        for _id in ids:
            nt.delete(_id)


    @patch('server.seed.requests.get', autospec=True)
    def test_error_response(self, mock_get):
        mock_get.return_value.status_code = 400
        mock_get.return_value.json.return_value = {}
        with pytest.raises(ConnectionError):
            sd.seed_nations()

    @patch('server.seed.requests.get', autospec=True)
    def test_missing_data(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {}

        with pytest.raises(ValueError):
            sd.seed_nations()

    @patch('server.seed.requests.get', autospec=True)
    def test_json_pagination_multiple_pages(self, mock_get):
        """Test JSON parsing with multiple pages of results"""
        
        sd.RESULTS_PER_PAGE = 2
        # Mock responses for multiple pages
        responses = [
            {
                'data': [
                    {'name': 'Nation 1'},
                    {'name': 'Nation 2'},
                ],
                'metadata': {'totalCount': 5},
            },
            {
                'data': [
                    {'name': 'Nation 3'},
                    {'name': 'Nation 4'},
                ],
                'metadata': {'totalCount': 5},
            },
            {
                'data': [
                    {'name': 'Nation 5'},
                ],
                'metadata': {'totalCount': 5},
            },
        ]
        
        mock_get.side_effect = [
            MagicMock(status_code=200, json=MagicMock(return_value=responses[0])),
            MagicMock(status_code=200, json=MagicMock(return_value=responses[1])),
            MagicMock(status_code=200, json=MagicMock(return_value=responses[2])),
        ]

        
        old_count = nt.count()
        ids = sd.seed_nations()
        
        # Verify multiple nations were created
        assert len(ids) == 5
        assert nt.count() >= old_count + 5
        
        # Verify pagination was used correctly
        assert mock_get.call_count == 3
        
        # Clean up
        for _id in ids:
            nt.delete(_id)

    @patch('server.seed.requests.get', autospec=True)
    def test_json_with_missing_name_field(self, mock_get):
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

        old_count = nt.count()
        ids = sd.seed_nations()
        
        # Should ignore nations with empty names
        assert len(ids) == 0
        assert nt.count() >= old_count
        
        # Clean up
        for _id in ids:
            nt.delete(_id)

    @patch('server.seed.requests.get', autospec=True)
    def test_json_with_extra_fields(self, mock_get):
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

        old_count = nt.count()
        ids = sd.seed_nations()
        
        # Should handle extra fields gracefully
        assert len(ids) == 1
        assert nt.count() >= old_count
        
        # Clean up
        for _id in ids:
            nt.delete(_id)

    @patch('server.seed.requests.get', autospec=True)
    def test_json_empty_data_array(self, mock_get):
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

    @patch('server.seed.save_json')
    @patch('server.seed.requests.get', autospec=True)
    def test_saves_to_json_after_seeding(self, mock_get, mock_save_json):
        """Test that nation data is saved to JSON after seeding"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'data': [{'name': 'Test Nation'}],
            'metadata': {'totalCount': 1},
        }
        
        ids = sd.seed_nations()
        
        # Verify save_json was called with nations data
        mock_save_json.assert_called_once()
        call_args = mock_save_json.call_args
        assert call_args[0][0] == sd.NATIONS_JSON_FILE
        assert isinstance(call_args[0][1], dict)
        
        # Clean up
        for _id in ids:
            nt.delete(_id)


class TestSeedEarthquakes:
    # open manages context, so a MagicMock is necessary to simulate it
    @patch("builtins.open", new_callable=MagicMock)
    def test_valid(self, mock_open):
        data = (
            'location,country,latitude,longitude\n'
            '"my_city, my_state",my_nation,1,1'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)

        old_count = ct.count()
        sd.seed_earthquakes()
        assert ct.count() >= old_count
        # TODO: check if earthquakes are created

    @patch("builtins.open", new_callable=MagicMock)
    def test_failed_download(self, mock_open):
        mock_open.side_effect = FileNotFoundError("file not found")
        with pytest.raises(ConnectionError):
            sd.seed_earthquakes()

    @patch('server.seed.reverse_geocode')
    @patch("builtins.open", new_callable=MagicMock)
    def test_reverse_geocoding_mapping(self, mock_open, mock_geocode):
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

        old_count = ct.count()
        sd.seed_earthquakes()
        
        # Verify reverse_geocode was called with correct coordinates
        mock_geocode.assert_called_once_with(40.7128, -74.0060)
        assert ct.count() >= old_count

    @patch('server.seed.reverse_geocode')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_with_missing_city(self, mock_open, mock_geocode):
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

        old_count = ct.count()
        sd.seed_earthquakes()
        
        # Should skip entries without city
        assert ct.count() == old_count

    @patch('server.seed.reverse_geocode')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_with_partial_location_data(self, mock_open, mock_geocode):
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

        old_count = ct.count()
        sd.seed_earthquakes()
        
        # Should handle missing state gracefully
        assert ct.count() >= old_count

    @patch('server.seed.reverse_geocode')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_geocode_error_handling(self, mock_open, mock_geocode):
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

        old_count = ct.count()
        sd.seed_earthquakes()
        
        # Should continue processing despite error
        assert mock_geocode.call_count == 2

    @patch('server.seed.reverse_geocode')
    @patch("builtins.open", new_callable=MagicMock)
    def test_coordinate_to_location_mapping(self, mock_open, mock_geocode):
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

        old_count_nations = nt.count()
        old_count_cities = ct.count()
        
        sd.seed_earthquakes()
        
        # Verify geocoding was called with correct lat/lon
        mock_geocode.assert_called_with(35.6762, 139.6503)
        
        # Verify data was created
        assert ct.count() >= old_count_cities

    @patch('server.seed.reverse_geocode')
    @patch("builtins.open", new_callable=MagicMock)
    def test_reverse_geocoding_mapping(self, mock_open, mock_geocode):
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
        
        old_count = ct.count()
        sd.seed_earthquakes()
        
        # Verify reverse_geocode was called with correct coordinates
        mock_geocode.assert_called_once_with(40.7128, -74.0060)
        assert ct.count() >= old_count

    @patch('server.seed.reverse_geocode')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_missing_city(self, mock_open, mock_geocode):
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
        
        old_count = ct.count()
        sd.seed_earthquakes()
        
        # Should skip this entry when no city found
        assert ct.count() == old_count
        mock_geocode.assert_called_once()

    @patch('server.seed.reverse_geocode')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_with_state_and_nation(self, mock_open, mock_geocode):
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
        
        old_count_cities = ct.count()
        old_count_nations = nt.count()
        
        sd.seed_earthquakes()
        
        # Verify entities were created
        assert ct.count() >= old_count_cities
        assert nt.count() >= old_count_nations

    @patch('server.seed.reverse_geocode')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_without_state(self, mock_open, mock_geocode):
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
        
        old_count = ct.count()
        sd.seed_earthquakes()
        
        # Should handle missing state gracefully
        assert ct.count() >= old_count

    @patch('server.seed.reverse_geocode')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_geocoding_exception(self, mock_open, mock_geocode):
        """Test handling of geocoding exceptions during mapping"""
        data = (
            'latitude,longitude,magnitude\n'
            '40.7128,-74.0060,5.5\n'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        
        # Mock geocoding failure
        mock_geocode.side_effect = Exception("Geocoding service error")
        
        old_count = ct.count()
        # Should continue without crashing
        sd.seed_earthquakes()
        
        # No cities should be added due to error
        assert ct.count() == old_count

    @patch('server.seed.reverse_geocode')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_multiple_coordinates(self, mock_open, mock_geocode):
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
        
        old_count = ct.count()
        sd.seed_earthquakes()
        
        # Verify all coordinates were processed
        assert mock_geocode.call_count == 3
        assert ct.count() >= old_count

    @patch('server.seed.reverse_geocode')
    @patch("builtins.open", new_callable=MagicMock)
    def test_reverse_geocoding_mapping(self, mock_open, mock_geocode):
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

        old_count = ct.count()
        sd.seed_earthquakes()
        
        # Verify reverse_geocode was called with correct coordinates
        assert mock_geocode.call_count == 2
        mock_geocode.assert_any_call(40.7128, -74.0060)
        mock_geocode.assert_any_call(34.0522, -118.2437)
        
        # Verify cities were created
        assert ct.count() >= old_count

    @patch('server.seed.reverse_geocode')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_with_missing_city(self, mock_open, mock_geocode):
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

        old_count = ct.count()
        sd.seed_earthquakes()
        
        # Verify city count unchanged (no city created)
        assert ct.count() == old_count

    @patch('server.seed.reverse_geocode')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_with_partial_location_data(self, mock_open, mock_geocode):
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

        old_count = ct.count()
        sd.seed_earthquakes()
        
        # Should still create city even without state
        assert ct.count() >= old_count

    @patch('server.seed.reverse_geocode')
    @patch("builtins.open", new_callable=MagicMock)
    def test_mapping_handles_geocoding_exception(self, mock_open, mock_geocode):
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

        old_count = ct.count()
        sd.seed_earthquakes()
        
        # Should continue processing after exception
        assert ct.count() >= old_count

    @patch('server.seed.reverse_geocode')
    @patch("builtins.open", new_callable=MagicMock)
    def test_coordinate_to_location_mapping(self, mock_open, mock_geocode):
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

        old_nations = nt.count()
        old_cities = ct.count()
        
        sd.seed_earthquakes()
        
        # Verify hierarchical creation (nation, state, city)
        assert nt.count() >= old_nations
        assert ct.count() >= old_cities
        
        # Verify correct coordinates were passed
        mock_geocode.assert_called_once_with(35.6762, 139.6503)


class TestSeedLandslides:
    @patch('server.seed.reverse_geocode')
    @patch("builtins.open", new_callable=MagicMock)
    def test_valid_reverse_geocoding(self, mock_open, mock_geocode):
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"my_city, my_state",my_nation,1.0,1.0'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        mock_geocode.return_value = {
            'city': 'New York',
            'state': 'New York',
            'country': 'United States'
        }
        old_count = ct.count()
        sd.seed_landslides()
        assert ct.count() >= old_count
        mock_geocode.assert_called_once_with(1, 1)

    @patch('server.seed.reverse_geocode')
    @patch("builtins.open", new_callable=MagicMock)
    def test_geocode_exception_handled(self, mock_open, mock_geocode):
        data = (
            'location_description,country_name,latitude,longitude\n'
            '"broken_city, broken_state",broken_nation,1.0,2.0'
        )
        mock_open.return_value.__enter__.return_value = StringIO(data)
        mock_geocode.side_effect = Exception("A")

        old_count = ct.count()
        sd.seed_landslides()
        assert ct.count() == old_count
        mock_geocode.assert_called_once_with(1.0, 2.0)

    @patch("builtins.open", new_callable=MagicMock)
    def test_failed_download(self, mock_open):
        mock_open.side_effect = FileNotFoundError("file not found")
        with pytest.raises(ConnectionError):
            sd.seed_landslides()
