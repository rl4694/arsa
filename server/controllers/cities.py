"""
This file implements CRUD operations for cities.
"""

from flask import request
from flask_restx import Resource, Namespace, fields
from server.controllers.crud import CRUD

CITIES_RESP = 'cities'
COLLECTION = 'cities'
NAME = 'name'
STATE_NAME = 'state_name'
NATION_NAME = 'nation_name'
LATITUDE = 'latitude'
LONGITUDE = 'longitude'
KEY = (NAME, STATE_NAME)

cities = CRUD(
    COLLECTION,
    KEY,
    {
        NAME: str,
        STATE_NAME: str,
        NATION_NAME: str,
	LATITUDE: float,
	LONGITUDE: float,
    }
)


api = Namespace('cities', description='Cities CRUD operations')

city_model = api.model('City', {
    NAME: fields.String(required=True, description='City Name'),
    STATE_NAME: fields.String(description='State Name'),
    NATION_NAME: fields.String(description='Nation Name'),
    LATITUDE: fields.Float(description='City Latitude'),
    LONGITUDE: fields.Float(description='City Longitude')
})


@api.route('/')
class CityList(Resource):
    """
    Handle collection-level operations for cities.
    Supports listing all cities and creating new ones.
    """
    @api.doc('list_cities')
    def get(self):
        """Return all cities."""
        return {CITIES_RESP: cities.read()}

    @api.expect(city_model)
    @api.doc('create_city')
    def post(self):
        """Create a new city."""
        data = request.json
        _id = cities.create(data, return_duplicate_id=False)
        created = cities.select(_id)
        return {CITIES_RESP: created}, 201


@api.route('/<string:city_id>')
class City(Resource):
    """
    Handle item-level operations for a single city.
    Supports retrieval, update, and deletion.
    """
    @api.doc('get_city')
    def get(self, city_id):
        """Retrieve a single city by ID."""
        try:
            record = cities.select(city_id)
            return {CITIES_RESP: record}
        except:
            api.abort(404, "City not found")

    @api.expect(city_model)
    @api.doc('update_city')
    def put(self, city_id):
        """Update a city by ID."""
        try:
            cities.update(city_id, request.json)
            record = cities.select(city_id)
            return {CITIES_RESP: record}
        except KeyError:
            api.abort(404, "City not found")

    @api.doc('delete_city')
    def delete(self, city_id):
        """Delete a city by ID."""
        try:
            cities.delete(city_id)
            return '', 204
        except KeyError:
            api.abort(404, "City not found")
