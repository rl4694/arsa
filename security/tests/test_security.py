import pytest
from unittest.mock import patch
from flask import Flask
import security.security as security

# Constants
NO_AUTH_EP = '/no_auth'
AUTH_EP = '/auth'
SUCCESS_RESP = b'ok'
FEATURE = 'feature1'
BYPASS_KEY = 'bypass-key'
VALID_TOKEN = 'valid-token'

# Create mock objects
class FakeSerializer:
    def loads(self, token, salt=None):
        if token != VALID_TOKEN:
            raise Exception('bad token')

mock_serializer = FakeSerializer()
mock_security_recs = {
    FEATURE: {
        security.READ: {
            security.CHECKS: {
                security.LOGIN: False
            }
        },
        security.CREATE: {
            security.CHECKS: {
                security.LOGIN: True
            }
        }
    }
}

# Create fixtures
@pytest.fixture(autouse=True)
def patch_dependencies():
    with (patch('security.security.AUTH_BYPASS_KEY', BYPASS_KEY),
          patch('security.security._serializer', mock_serializer),
          patch('security.security.security_recs', mock_security_recs)):
        yield

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True

    @app.route(NO_AUTH_EP)
    @security.require_auth(FEATURE, security.READ)
    def no_auth_route():
        return SUCCESS_RESP

    @app.route(AUTH_EP)
    @security.require_auth(FEATURE, security.CREATE)
    def auth_route():
        return SUCCESS_RESP

    return app


# Unit tests
def test_read():
    recs = security.read()
    assert isinstance(recs, dict)
    for feature in recs:
        assert isinstance(feature, str)
        assert len(feature) > 0

def test_no_auth_no_token(app):
    res = app.test_client().get(NO_AUTH_EP)
    assert res.status_code == 200
    assert res.data == SUCCESS_RESP

def test_no_auth_has_token(app):
    res = app.test_client().get(NO_AUTH_EP, headers={
        'Authorization': f'Bearer {VALID_TOKEN}',
    })
    assert res.status_code == 200
    assert res.data == SUCCESS_RESP

def test_auth_no_token(app):
    res = app.test_client().get(AUTH_EP)
    assert res.status_code == 401

def test_auth_has_token(app):
    res = app.test_client().get(AUTH_EP, headers={
        'Authorization': f'Bearer {VALID_TOKEN}',
    })
    assert res.status_code == 200
    assert res.data == SUCCESS_RESP

def test_bypass_key(app):
    res = app.test_client().get(AUTH_EP, headers={
        'Authorization': BYPASS_KEY
    })
    assert res.status_code == 200
    assert res.data == SUCCESS_RESP