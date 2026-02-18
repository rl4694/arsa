"""
This is the file containing all of the endpoints for our flask app.
The endpoint called `endpoints` will return all available endpoints.
"""
# from http import HTTPStatus
from flask import Flask, request
from flask_restx import Resource, Api, fields
from flask_cors import CORS
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from server.controllers.cities import api as cities_ns
from server.controllers.states import api as states_ns
from server.controllers.nations import api as nations_ns
from server.controllers.natural_disasters import api as disasters_ns
from server.controllers.users import api as users_ns
from server.etl.geocoding import reverse_geocode

# import werkzeug.exceptions as wz

app = Flask(__name__)
CORS(app)
api = Api(app)

api.add_namespace(cities_ns, path='/cities')
api.add_namespace(states_ns, path='/states')
api.add_namespace(nations_ns, path='/nations')
api.add_namespace(disasters_ns, path='/natural_disasters')
api.add_namespace(users_ns, path='/users')

ENDPOINT_EP = '/endpoints'
ENDPOINT_RESP = 'Available endpoints'

HELLO_EP = '/hello'
HELLO_RESP = 'hello'
MESSAGE = 'Message'

GEOCODE_EP = '/geocode'
location_model = api.model('Location', {
    'city': fields.String(description='City name'),
    'state': fields.String(description='State/Province name'),
    'country': fields.String(description='Country name'),
    'country_code': fields.String(description='Country code'),
    'latitude': fields.Float(description='Latitude'),
    'longitude': fields.Float(description='Longitude'),
    'display_name': fields.String(description='Full address')
})


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


@api.route(GEOCODE_EP)
class GeocodeResource(Resource):
    @api.doc('reverse_geocode',
             params={
                 'lat': 'Latitude (required, between -90 and 90)',
                 'lon': 'Longitude (required, between -180 and 180)'
             })
    @api.response(200, 'Success', location_model)
    @api.response(400, 'Bad Request - Invalid or missing parameters')
    @api.response(503, 'Service Unavailable - Geocoding service error')
    def get(self):
        """
        Convert coordinates to location information.

        Query parameters:
        - lat: Latitude (required)
        - lon: Longitude (required)

        Example: /geocode?lat=40.7128&lon=-74.0060
        """
        # Get query parameters
        lat_str = request.args.get('lat')
        lon_str = request.args.get('lon')

        # Validate required parameters
        if lat_str is None or lon_str is None:
            api.abort(400, "Both 'lat' and 'lon' parameters are required")

        # Convert to float
        try:
            lat = float(lat_str)
            lon = float(lon_str)
        except ValueError:
            api.abort(400, "Latitude and longitude must be valid numbers")

        # Perform reverse geocoding
        try:
            result = reverse_geocode(lat, lon)
            return result, 200
        except ValueError as e:
            api.abort(400, str(e))
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            api.abort(503, str(e))
