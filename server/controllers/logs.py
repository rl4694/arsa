"""
Developer endpoint for retrieving recent server log entries.

On PythonAnywhere the error, server, and access logs live under /var/log/.
Locally the app writes to arsa.log via the RotatingFileHandler in endpoints.py.
get_log_paths() picks the right sources automatically.
"""
import os
from flask import request
from flask_restx import Resource, Namespace
import security.security as security
from server.env import get_env

SECURITY_FEATURE = 'logs'
LOGS_RESP = 'logs'
# Used by endpoints.py to configure the local RotatingFileHandler
LOG_FILE = get_env('LOG_FILE', 'arsa.log')
# PythonAnywhere log paths
PA_ERROR_LOG = '/var/log/arsa.pythonanywhere.com.error.log'
PA_SERVER_LOG = '/var/log/arsa.pythonanywhere.com.server.log'
PA_ACCESS_LOG = '/var/log/arsa.pythonanywhere.com.access.log'
PA_LOGS = [PA_ERROR_LOG, PA_SERVER_LOG, PA_ACCESS_LOG]
DEFAULT_LINES = 100
MAX_LINES = 500

api = Namespace('logs', description='Developer log access')


def get_log_paths():
    """
    Return the list of log file paths to serve.

    Priority:
    1. LOG_FILE env var — explicit override for any environment
    2. PythonAnywhere logs — all that exist under /var/log/
    3. arsa.log — local rotating log written by the RotatingFileHandler
    """
    env_override = get_env('LOG_FILE', '')
    if env_override:
        return [env_override]
    pa_logs = [p for p in PA_LOGS if os.path.isfile(p)]
    if pa_logs:
        return pa_logs
    return ['arsa.log']


@api.route('/', strict_slashes=False)
class LogList(Resource):
    @security.require_auth(SECURITY_FEATURE, security.READ)
    @api.doc('get_logs',
             params={'n': f'Number of log lines to return (default {DEFAULT_LINES}, max {MAX_LINES})'})
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized')
    def get(self):
        """Return recent logs, concatenating error, server, and access logs."""
        try:
            n = min(int(request.args.get('n', DEFAULT_LINES)), MAX_LINES)
        except (ValueError, TypeError):
            n = DEFAULT_LINES

        all_lines = []
        for path in get_log_paths():
            if not os.path.isfile(path):
                continue
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines.extend(f.readlines())

        return {LOGS_RESP: [ln.rstrip('\n') for ln in all_lines[-n:]]}
