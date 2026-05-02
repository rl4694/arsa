# server/controllers/tests/test_logs.py
import pytest
from unittest.mock import patch
from itsdangerous import URLSafeTimedSerializer

from server.controllers.logs import get_log_paths, PA_ERROR_LOG, PA_SERVER_LOG, PA_ACCESS_LOG, DEFAULT_LINES, MAX_LINES


# Helpers

def make_token(secret='arsa-dev-secret'):
    """Generate a valid Bearer token using the default dev secret."""
    s = URLSafeTimedSerializer(secret)
    return s.dumps({'name': 'dev', 'email': 'dev@test.com'}, salt='auth')


@pytest.fixture
def client():
    from server.endpoints import app
    app.testing = True
    return app.test_client()


@pytest.fixture
def auth_headers():
    return {'Authorization': f'Bearer {make_token()}'}


# get_log_paths() unit tests

class TestGetLogPaths:
    def test_returns_local_log_when_pa_logs_absent(self, monkeypatch):
        """Falls back to arsa.log when no PA logs are on disk."""
        monkeypatch.delenv('LOG_FILE', raising=False)
        with patch('os.path.isfile', return_value=False):
            result = get_log_paths()
        assert result == ['arsa.log']

    def test_returns_all_pa_logs_when_present(self, monkeypatch):
        """Returns all three PA logs when they all exist."""
        monkeypatch.delenv('LOG_FILE', raising=False)
        with patch('os.path.isfile', side_effect=lambda p: p in (PA_ERROR_LOG, PA_SERVER_LOG, PA_ACCESS_LOG)):
            result = get_log_paths()
        assert result == [PA_ERROR_LOG, PA_SERVER_LOG, PA_ACCESS_LOG]

    def test_returns_only_existing_pa_logs(self, monkeypatch):
        """Only includes PA log files that actually exist on disk."""
        monkeypatch.delenv('LOG_FILE', raising=False)
        with patch('os.path.isfile', side_effect=lambda p: p == PA_ERROR_LOG):
            result = get_log_paths()
        assert result == [PA_ERROR_LOG]

    def test_env_override_beats_pa_logs(self, monkeypatch):
        """LOG_FILE env var wins even when the PA logs exist."""
        custom = '/tmp/custom_override.log'
        monkeypatch.setenv('LOG_FILE', custom)
        with patch('os.path.isfile', return_value=True):
            result = get_log_paths()
        assert result == [custom]

    def test_env_override_beats_local_fallback(self, monkeypatch):
        """LOG_FILE env var wins when the PA logs are absent."""
        custom = '/tmp/another_override.log'
        monkeypatch.setenv('LOG_FILE', custom)
        with patch('os.path.isfile', return_value=False):
            result = get_log_paths()
        assert result == [custom]


# GET /logs/ endpoint tests

class TestLogsEndpoint:
    def test_returns_401_without_token(self, client):
        """Endpoint must reject unauthenticated requests."""
        with patch('security.security.AUTH_BYPASS_KEY', 'non-empty-bypass'):
            response = client.get('/logs/')
        assert response.status_code == 401

    def test_returns_log_lines(self, client, auth_headers, tmp_path):
        """Returns the lines from the resolved log file."""
        log_file = tmp_path / 'test.log'
        log_file.write_text('line1\nline2\nline3\n')

        with patch('server.controllers.logs.get_log_paths', return_value=[str(log_file)]):
            response = client.get('/logs/', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['logs'] == ['line1', 'line2', 'line3']

    def test_concatenates_multiple_logs(self, client, auth_headers, tmp_path):
        """Lines from multiple log files are concatenated in order."""
        log_a = tmp_path / 'a.log'
        log_b = tmp_path / 'b.log'
        log_a.write_text('a1\na2\n')
        log_b.write_text('b1\nb2\n')

        with patch('server.controllers.logs.get_log_paths', return_value=[str(log_a), str(log_b)]):
            response = client.get('/logs/', headers=auth_headers)

        assert response.status_code == 200
        assert response.get_json()['logs'] == ['a1', 'a2', 'b1', 'b2']

    def test_returns_empty_list_when_file_missing(self, client, auth_headers):
        """Returns an empty list when the log file does not exist."""
        with patch('server.controllers.logs.get_log_paths', return_value=['/nonexistent/path.log']):
            response = client.get('/logs/', headers=auth_headers)

        assert response.status_code == 200
        assert response.get_json()['logs'] == []

    def test_n_param_limits_lines(self, client, auth_headers, tmp_path):
        """?n=2 returns only the last 2 lines."""
        log_file = tmp_path / 'test.log'
        log_file.write_text('\n'.join(f'line{i}' for i in range(10)) + '\n')

        with patch('server.controllers.logs.get_log_paths', return_value=[str(log_file)]):
            response = client.get('/logs/?n=2', headers=auth_headers)

        data = response.get_json()
        assert len(data['logs']) == 2
        assert data['logs'] == ['line8', 'line9']

    def test_n_param_capped_at_max(self, client, auth_headers, tmp_path):
        """?n values above MAX_LINES are silently capped."""
        log_file = tmp_path / 'test.log'
        log_file.write_text('\n'.join(f'line{i}' for i in range(MAX_LINES + 50)) + '\n')

        with patch('server.controllers.logs.get_log_paths', return_value=[str(log_file)]):
            response = client.get(f'/logs/?n={MAX_LINES + 200}', headers=auth_headers)

        data = response.get_json()
        assert len(data['logs']) == MAX_LINES

    def test_invalid_n_uses_default(self, client, auth_headers, tmp_path):
        """Non-numeric ?n falls back to DEFAULT_LINES."""
        log_file = tmp_path / 'test.log'
        log_file.write_text('\n'.join(f'line{i}' for i in range(DEFAULT_LINES + 50)) + '\n')

        with patch('server.controllers.logs.get_log_paths', return_value=[str(log_file)]):
            response = client.get('/logs/?n=notanumber', headers=auth_headers)

        data = response.get_json()
        assert len(data['logs']) == DEFAULT_LINES

    def test_strips_trailing_newlines(self, client, auth_headers, tmp_path):
        """Lines have their trailing newline characters removed."""
        log_file = tmp_path / 'test.log'
        log_file.write_text('alpha\nbeta\n')

        with patch('server.controllers.logs.get_log_paths', return_value=[str(log_file)]):
            response = client.get('/logs/', headers=auth_headers)

        for line in response.get_json()['logs']:
            assert not line.endswith('\n')
