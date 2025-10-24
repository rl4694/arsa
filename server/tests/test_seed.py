import pytest
import time
from io import StringIO
from unittest.mock import patch, MagicMock
from server import cities as ct
from server import nations as nt
from server import seed as sd


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
    def test_error_response(self, mock_get, mock_sleep):
        mock_get.return_value.status_code = 400
        with pytest.raises(ConnectionError):
            sd.seed_cities(sd.RESULTS_PER_PAGE)
    
    @patch('time.sleep')
    @patch('server.seed.requests.get', autospec=True)
    def test_missing_data(self, mock_get, mock_sleep):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {}

        with pytest.raises(ValueError):
            sd.seed_cities(sd.RESULTS_PER_PAGE)

    def test_negative_num_cities(self):
        with pytest.raises(ValueError):
            sd.seed_cities(-1)

    def test_non_int_num_cities(self):
        with pytest.raises(ValueError):
            sd.seed_cities('test')


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


class TestSeedEarthquakes:
    # open manages context, so a MagicMock is necessary to simulate it
    @patch('server.seed.os.remove')
    @patch('server.seed.KaggleApi')
    @patch("builtins.open", new_callable=MagicMock)
    def test_valid(self, mock_open, mock_kaggle_api, mock_remove):
        data = 'location,country\n"my_city,my_state",my_nation'
        mock_open.return_value.__enter__.return_value = StringIO(data)
        sd.seed_earthquakes()
        # TODO: check if earthquakes are created

    @patch('server.seed.os.remove')
    @patch('server.seed.KaggleApi')
    @patch("builtins.open", new_callable=MagicMock)
    def test_failed_download(self, mock_open, mock_kaggle_api, mock_remove):
        mock_open.side_effect = FileNotFoundError("file not found")
        with pytest.raises(ConnectionError):
            sd.seed_earthquakes()
