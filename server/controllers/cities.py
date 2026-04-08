"""
This file implements CRUD operations for cities.
"""

from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
from numbers import Real
import server.controllers.crud as crud
from server.controllers.users import require_auth

CITIES_RESP = 'records'
COLLECTION = 'cities'
NAME = 'name'
STATE_NAME = 'state_name'
NATION_NAME = 'nation_name'
LATITUDE = 'latitude'
LONGITUDE = 'longitude'
KEY = (NAME, STATE_NAME)

cities = crud.CRUD(
    COLLECTION,
    KEY,
    {
        NAME: str,
        STATE_NAME: str,
        NATION_NAME: str,
        LATITUDE: Real,
        LONGITUDE: Real,
    }
)


api = Namespace('cities', description='Cities CRUD operations')

city_model = api.model('City', {
    NAME: fields.String(required=True, description='City Name'),
    STATE_NAME: fields.String(description='State Name'),
    NATION_NAME: fields.String(description='Nation Name'),
    LATITUDE: fields.Float(description='City Latitude', default=0.5),
    LONGITUDE: fields.Float(description='City Longitude', default=0.5)
})


@api.route('/', strict_slashes=False)
class CityList(Resource):
    """
    Handle collection-level operations for cities.
    Supports listing all cities and creating new ones.
    """
    @api.doc('list_cities')
    def get(self):
        """Return all cities."""
        return {CITIES_RESP: cities.read()}

    @require_auth
    @api.expect(city_model)
    @api.doc('create_city')
    def post(self):
        """Create a new city."""
        data = request.json
        _id = cities.create(data)
        created = cities.select(_id)
        return {CITIES_RESP: created}, 201


@api.route('/fields')
class CityFields(Resource):
    @api.doc('get_fields')
    def get(self):
        """Get field information for cities."""
        return [
            { crud.ATTRIBUTE: NAME, crud.DISPLAY: "City Name", crud.TYPE: "text" },
            { crud.ATTRIBUTE: STATE_NAME, crud.DISPLAY: "State Name", crud.TYPE: "text" },
            { crud.ATTRIBUTE: NATION_NAME, crud.DISPLAY: "Nation Name", crud.TYPE: "text" },
            { crud.ATTRIBUTE: LATITUDE, crud.DISPLAY: "Latitude", crud.TYPE: "number" },
            { crud.ATTRIBUTE: LONGITUDE, crud.DISPLAY: "Longitude", crud.TYPE: "number" },
        ]


@api.route('/<string:city_id>')
class City(Resource):
    """
    Handle item-level operations for a single city.
    Supports retrieval, update, and deletion.
    """
    @api.doc('get_city')
    def get(self, city_id):
        """Retrieve a single city by ID."""
        record = cities.select(city_id)
        return {CITIES_RESP: record}

    @require_auth
    @api.expect(city_model)
    @api.doc('update_city')
    def put(self, city_id):
        """Update a city by ID."""
        cities.update(city_id, request.json)
        record = cities.select(city_id)
        return {CITIES_RESP: record}

    @require_auth
    @api.doc('delete_city')
    def delete(self, city_id):
        """Delete a city by ID."""
        cities.delete(city_id)
        return '', 204
