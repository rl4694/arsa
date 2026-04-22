"""
Developer endpoint for retrieving recent server log entries.

On PythonAnywhere the error log lives at PA_ERROR_LOG.  Locally the app
writes to arsa.log via the RotatingFileHandler set up in endpoints.py.
get_log_path() picks the right source automatically.
"""
import os
from flask import request
from flask_restx import Resource, Namespace
import security.security as security
from dotenv import load_dotenv

load_dotenv()

SECURITY_FEATURE = 'logs'
LOGS_RESP = 'logs'
# Used by endpoints.py to configure the local RotatingFileHandler
LOG_FILE = os.environ.get('LOG_FILE', 'arsa.log')
# PythonAnywhere writes the WSGI error log here
PA_ERROR_LOG = '/var/log/arsa.pythonanywhere.com.error.log'
DEFAULT_LINES = 100
MAX_LINES = 500

api = Namespace('logs', description='Developer log access')


def get_log_path():
    """
    Return the path of the log file to serve.

    Priority:
    1. LOG_FILE env var — explicit override for any environment
    2. PythonAnywhere error log — used automatically when running on PA
    3. arsa.log — local rotating log written by the RotatingFileHandler
    """
    env_override = os.environ.get('LOG_FILE')
    if env_override:
        return env_override
    if os.path.isfile(PA_ERROR_LOG):
        return PA_ERROR_LOG
    return 'arsa.log'


@api.route('/', strict_slashes=False)
class LogList(Resource):
    @security.require_auth(SECURITY_FEATURE, security.READ)
    @api.doc('get_logs',
             params={'n': f'Number of log lines to return (default {DEFAULT_LINES}, max {MAX_LINES})'})
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized')
    def get(self):
        """Return recent server log entries from the log file."""
        try:
            n = min(int(request.args.get('n', DEFAULT_LINES)), MAX_LINES)
        except (ValueError, TypeError):
            n = DEFAULT_LINES

        log_path = get_log_path()
        if not os.path.isfile(log_path):
            return {LOGS_RESP: []}

        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        return {LOGS_RESP: [ln.rstrip('\n') for ln in lines[-n:]]}
