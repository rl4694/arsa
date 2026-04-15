"""
Developer endpoint for retrieving recent server log entries.
"""
import os
from flask import request
from flask_restx import Resource, Namespace
from server.controllers.users import require_auth

LOGS_RESP = 'logs'
LOG_FILE = os.environ.get('LOG_FILE', 'arsa.log')
DEFAULT_LINES = 100
MAX_LINES = 500

api = Namespace('logs', description='Developer log access')


@api.route('/', strict_slashes=False)
class LogList(Resource):
    @require_auth
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

        if not os.path.isfile(LOG_FILE):
            return {LOGS_RESP: []}

        with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        return {LOGS_RESP: [ln.rstrip('\n') for ln in lines[-n:]]}
