"""
This is the file containing all of the endpoints for our flask app.
The endpoint called `endpoints` will return all available endpoints.
"""
# from http import HTTPStatus
from flask import Flask, request
from flask_restx import Resource, Api, fields  # Namespace
from flask_cors import CORS
from server import cities as ct

# import werkzeug.exceptions as wz

app = Flask(__name__)
CORS(app)
api = Api(app)

ENDPOINT_EP = '/endpoints'
ENDPOINT_RESP = 'Available endpoints'

HELLO_EP = '/hello'
HELLO_RESP = 'hello'
MESSAGE = 'Message'

CITIES_EP = '/cities'
CITIES_RESP = 'cities'


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


city_model = api.model(
    'City',
    {
        'name': fields.String(required=True, description='City Name')
    }
)


@api.route(CITIES_EP)
class CityList(Resource):
    @api.doc('list_cities')
    def get(self):
        cities = ct.read()
        return {
            CITIES_RESP: cities,
        }

    @api.expect(city_model)
    @api.doc('create_city')
    def post(self):
        data = request.json
        city_id = ct.create(data)
        return {'id': city_id, **data}, 201


@api.route('/cities/<string:city_id>')
class City(Resource):
    @api.doc('get_city')
    def get(self, city_id):
        city = ct.cities.get(city_id)
        if not city:
            api.abort(404, "City not found")
        return {'id': city_id, **city}

    @api.expect(city_model)
    @api.doc('update_city')
    def put(self, city_id):
        if city_id not in ct.cities:
            api.abort(404, "City not found")
        data = request.json
        ct.cities[city_id] = data
        return {'id': city_id, **data}

    @api.doc('delete_city')
    def delete(self, city_id):
        if city_id not in ct.cities:
            api.abort(404, "City not found")
        del ct.cities[city_id]
        return '', 204
