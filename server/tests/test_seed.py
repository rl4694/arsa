import pytest
import time
from unittest.mock import patch
from server import cities as ct
from server import seed as sd


class TestFetchCities:
    @patch('server.seed.requests.get', autospec=True)
    def test_error_response(self, mock_get):
        mock_get.return_value.status_code = 400
        with pytest.raises(ConnectionError):
            sd.fetch_cities(0)

    def test_negative_offset(self):
        with pytest.raises(ValueError):
            sd.fetch_cities(-1)


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

    def test_negative_cities(self):
        with pytest.raises(ValueError):
            sd.seed_cities(-1)
