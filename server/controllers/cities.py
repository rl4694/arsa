"""
This file implements CRUD operations for cities.
"""

from flask import request
from flask_restx import Resource, Namespace, fields
from bson.objectid import ObjectId
from server.controllers.cache import Cache
import data.db_connect as dbc

COLLECTION = 'cities'
NAME = 'name'
STATE = 'state'
NATION = 'nation'
cache = Cache(COLLECTION, (NAME, STATE))


def length() -> int:
    return len(cache.read())


def create(fields: dict, recursive=True) -> str:
    if not isinstance(fields, dict):
        raise ValueError(f'Bad type for fields: {type(fields)}')
    if not fields.get(NAME):
        raise ValueError(f'Name missing in fields: {fields.get(NAME)}')

    name = fields[NAME].strip().lower()
    state = fields.get(STATE, "").strip().lower()
    cities = cache.read()

    if (name, state) in cities:
        if recursive:
            return str(cities[(name, state)]['_id'])
        else:
            raise ValueError("Duplicate city detected and recursive not allowed.")

    result = dbc.create(COLLECTION, {
        NAME: name,
        STATE: fields.get(STATE),
        NATION: fields.get(NATION)
    })
    cache.reload()
    return str(result.inserted_id)


def read() -> dict:
    return cache.read()


def update(name: str, state: str, data: dict):
    result = dbc.update(COLLECTION, {NAME: name, STATE: state}, data)
    if result.matched_count == 0:
        raise KeyError("City not found")
    cache.reload()


def delete(name: str, state: str):
    deleted_count = dbc.delete(COLLECTION, {NAME: name, STATE: state})
    if deleted_count == 0:
        raise KeyError("City not found")
    cache.reload()


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
        return {'cities': read()}

    @api.expect(city_model)
    @api.doc('create_city')
    def post(self):
        data = request.json
        recursive = data.get('recursive', True)
        city_id = create(data, recursive=recursive)
        return {'id': city_id, **data}, 201


@api.route('/<string:city_id>')
class City(Resource):
    @api.doc('get_city')
    def get(self, city_id):
        city = dbc.read_one(COLLECTION, {'_id': ObjectId(city_id)})
        if not city:
            api.abort(404, "City not found")
        return {'id': city_id, **city}

    @api.expect(city_model)
    @api.doc('update_city')
    def put(self, city_id):
        try:
            update(city_id, request.json)
            city = dbc.read_one(COLLECTION, {'_id': ObjectId(city_id)})
            return {'id': city_id, **city}
        except KeyError:
            api.abort(404, "City not found")

    @api.doc('delete_city')
    def delete(self, city_id):
        try:
            delete(city_id)
            return '', 204
        except KeyError:
            api.abort(404, "City not found")
