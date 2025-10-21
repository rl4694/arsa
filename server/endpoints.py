"""
This is the file containing all of the endpoints for our flask app.
The endpoint called `endpoints` will return all available endpoints.
"""
# from http import HTTPStatus
from flask import Flask, # request
from flask_restx import Resource, Api, # fields, Namespace
from flask_cors import CORS

from server.cities import api as cities_ns

# import werkzeug.exceptions as wz

app = Flask(__name__)
CORS(app)
api = Api(app)

api.add_namespace(cities_ns, path='/cities')

ENDPOINT_EP = '/endpoints'
ENDPOINT_RESP = 'Available endpoints'

HELLO_EP = '/hello'
HELLO_RESP = 'hello'
MESSAGE = 'Message'


@api.route(HELLO_EP)
class HelloWorld(Resource):
    """
    The purpose of the HelloWorld class is to have a simple test to see if the
    app is working at all.
    """
    def get(self):
        """
        A trivial endpoint to see if the server is running.
        """
        return {HELLO_RESP: 'world'}


@api.route(ENDPOINT_EP)
class Endpoints(Resource):
    """
    This class will serve as live, fetchable documentation of what endpoints
    are available in the system.
    """
    def get(self):
        """
        The `get()` method will return a sorted list of available endpoints.
        """
        endpoints = sorted(rule.rule for rule in api.app.url_map.iter_rules())
        return {"Available endpoints": endpoints}
