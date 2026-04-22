from functools import wraps
from flask import request
from flask_restx import abort
from itsdangerous import URLSafeTimedSerializer
import os
from dotenv import load_dotenv

load_dotenv()

# import data.db_connect as dbc

"""
Our record format to meet our requirements (see security.md) will be:

{
    feature_name1: {
        create: {
            user_list: [],
            checks: {
                login: True,
                ip_address: False,
                dual_factor: False,
                # etc.
            },
        },
        read: {
            user_list: [],
            checks: {
                login: True,
                ip_address: False,
                dual_factor: False,
                # etc.
            },
        },
        update: {
            user_list: [],
            checks: {
                login: True,
                ip_address: False,
                dual_factor: False,
                # etc.
            },
        },
        delete: {
            user_list: [],
            checks: {
                login: True,
                ip_address: False,
                dual_factor: False,
                # etc.
            },
        },
    },
    feature_name2: # etc.
}
"""

AUTH_BYPASS_KEY = os.environ.get("AUTH_BYPASS_KEY", "")
SECRET_KEY = os.environ.get('SECRET_KEY', 'arsa-dev-secret')
COLLECT_NAME = 'security'
CREATE = 'create'
READ = 'read'
UPDATE = 'update'
DELETE = 'delete'
USER_LIST = 'user_list'
CHECKS = 'checks'
LOGIN = 'login'

# Features:
CITIES = 'cities'
STATES = 'states'
NATIONS = 'nations'
DISASTERS = 'disasters'
LOGS = 'logs'

security_recs = None
crud_permissions = {
    CREATE: {
        CHECKS: { LOGIN: True },
    },
    READ: {
        CHECKS: { LOGIN: False },
    },
    UPDATE: {
        CHECKS: { LOGIN: True },
    },
    DELETE: {
        CHECKS: { LOGIN: True },
    },
}
temp_recs = {
    CITIES: crud_permissions,
    STATES: crud_permissions,
    NATIONS: crud_permissions,
    DISASTERS: crud_permissions,
    LOGS: {
        READ: {
            CHECKS: { LOGIN: True },
        }
    }
}
_serializer = URLSafeTimedSerializer(SECRET_KEY)


def read() -> dict:
    global security_recs
    # dbc.read()
    security_recs = temp_recs
    return security_recs


def needs_recs(fn):
    """
    Should be used to decorate any function that directly accesses sec recs.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        global security_recs
        if not security_recs:
            security_recs = read()
        return fn(*args, **kwargs)
    return wrapper


@needs_recs
def read_feature(feature_name: str) -> dict:
    if feature_name in security_recs:
        return security_recs[feature_name]
    else:
        return None

@needs_recs
def require_auth(feature, operation):
    def decorator(f):
        """Decorator that validates the Bearer token on protected routes."""
        @wraps(f)
        def decorated(*args, **kwargs):
            checks = security_recs.get(feature).get(operation).get(CHECKS)
            if checks.get(LOGIN):
                auth_header = request.headers.get('Authorization', '')
                # If bypass key was passed, skip authorization
                if auth_header == AUTH_BYPASS_KEY:
                    return f(*args, **kwargs)

                # Check if bearer token is valid
                if not auth_header.startswith('Bearer '):
                    abort(401, 'Authorization token required')
                token = auth_header[len('Bearer '):]
                
                try:
                    _serializer.loads(token, salt='auth')
                except Exception:
                    abort(401, 'Invalid or expired token')
            return f(*args, **kwargs)
        return decorated
    return decorator
