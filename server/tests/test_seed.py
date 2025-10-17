import pytest
import time
from unittest.mock import patch
from server import cities as ct
from server import nations as nt
from server import seed as sd


class TestFetchRapidApi:
    @patch('server.seed.requests.get', autospec=True)
    def test_valid(self, mock_get):
        data = { 'hello': 'world' }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = data
        res = sd.fetch_rapid_api(sd.CITIES_URL, {})
        assert res == data

    @patch('server.seed.requests.get', autospec=True)
    def test_error_code(self, mock_get):
        mock_get.return_value.status_code = 400
        with pytest.raises(ConnectionError):
            sd.fetch_rapid_api(sd.CITIES_URL, {})


class TestSeedCities:
    @patch('time.sleep')
    @patch('server.seed.requests.get', autospec=True)
    def test_valid(self, mock_get, mock_sleep):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'data': [{
                'name': 'my city',
                'region': 'my state',
                'country': 'my country',
            }]
        }

        old_count = ct.length()
        sd.seed_cities(sd.RESULTS_PER_PAGE)
        assert ct.length() > old_count
    
    @patch('time.sleep')
    @patch('server.seed.requests.get', autospec=True)
    def test_missing_data(self, mock_get, mock_sleep):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {}

        with pytest.raises(ValueError):
            sd.seed_cities(sd.RESULTS_PER_PAGE)

    def test_negative_cities(self):
        with pytest.raises(ValueError):
            sd.seed_cities(-1)


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
        sd.seed_nations()
        assert nt.length() > old_count
    
    @patch('time.sleep')
    @patch('server.seed.requests.get', autospec=True)
    def test_missing_data(self, mock_get, mock_sleep):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {}

        with pytest.raises(ValueError):
            sd.seed_nations()
