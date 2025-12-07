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
KEY = (NAME,)

cities = CRUD(
    COLLECTION,
    KEY,
    {
        NAME: str,
        STATE_NAME: str,
        NATION_NAME: str,
    }
)


api = Namespace('cities', description='Cities CRUD operations')

city_model = api.model('City', {
    'name': fields.String(required=True, description='City Name'),
    'state': fields.String(description='State Name'),
    'nation': fields.String(description='Nation Name')
})


@api.route('/')
class CityList(Resource):
    @api.doc('list_cities')
    def get(self):
        records = cities.read()
        return {CITIES_RESP: list(records.values())}

    @api.expect(city_model)
    @api.doc('create_city')
    def post(self):
        data = request.json
        _id = cities.create(data, recursive=False)
        created = cities.select(_id)
        return {CITIES_RESP: created}, 201


@api.route('/<string:city_id>')
class City(Resource):
    @api.doc('get_city')
    def get(self, city_id):
        try:
            record = cities.select(city_id)
            return {CITIES_RESP: record}
        except:
            api.abort(404, "City not found")

    @api.expect(city_model)
    @api.doc('update_city')
    def put(self, city_id):
        try:
            cities.update(city_id, request.json)
            record = cities.select(city_id)
            return {CITIES_RESP: record}
        except KeyError:
            api.abort(404, "City not found")

    @api.doc('delete_city')
    def delete(self, city_id):
        try:
            cities.delete(city_id)
            return '', 204
        except KeyError:
            api.abort(404, "City not found")
