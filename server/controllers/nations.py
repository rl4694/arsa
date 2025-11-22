"""
This file implements CRUD operations for nations.
"""

from flask import request
from flask_restx import Resource, Namespace, fields
from bson.objectid import ObjectId
from server.controllers.cache import Cache
import data.db_connect as dbc

COLLECTION = 'nations'
NAME = 'name'
KEY = (NAME,)
cache = Cache(COLLECTION, KEY)


# Return the number of nations currently stored.
def length():
    return len(cache.read())

# Create a new nation record and return its id.
def create(fields: dict, recursive=True) -> str:
    if not isinstance(fields, dict):
        raise ValueError(f'Bad type for fields: {type(fields)}')
    if not fields.get(NAME):
        raise ValueError(f'Name missing in fields: {fields.get(NAME)}')

    name = fields[NAME].strip().lower()
    nations = cache.read()

    if (name,) in nations:
        if recursive:
            return str(nations[(name,)]['_id'])
        else:
            raise ValueError("Duplicate nation detected and recursive not allowed.")

    result = dbc.create(COLLECTION, {NAME: name})
    cache.reload()
    return str(result.inserted_id)

# Return the nations store as a dictionary.
def read() -> dict:
    return cache.read()


# Update an existing nation's data.
def update(key: tuple, fields: dict):
    if not isinstance(fields, dict):
        raise ValueError(f'Bad type for fields: {type(fields)}')
    if not isinstance(key, tuple) or len(key) < len(KEY):
        raise ValueError(f'Key must be a tuple of length {len(KEY)}: {key}')

    result = dbc.update(COLLECTION, {NAME: key[0]}, fields)
    if result.matched_count == 0:
        raise KeyError("Nation not found")
    cache.reload()


# Delete a nation by id.
def delete(key: tuple):
    if not isinstance(key, tuple) or len(key) < len(KEY):
        raise ValueError(f'Key must be a tuple of length {len(KEY)}: {key}')

    deleted_count = dbc.delete(COLLECTION, {NAME: key[0]})
    if deleted_count == 0:
        raise KeyError("Nation not found")
    cache.reload()


api = Namespace('nations', description='Nations CRUD operations')

nation_model = api.model('Nation', {
    'name': fields.String(required=True, description='Nation Name')
})


# NATIONS ENDPOINTS
@api.route('/')
class NationList(Resource):
    @api.doc('list_nations')
    def get(self):
        return {'nations': read()}

    @api.expect(nation_model)
    @api.doc('create_nation')
    def post(self):
        data = request.json
        recursive = data.get('recursive', True)
        nation_id = create(data, recursive=recursive)
        return {'id': nation_id, **data}, 201


@api.route('/<string:nation_id>')
class Nation(Resource):
    @api.doc('get_nation')
    def get(self, nation_id):
        nation = dbc.read_one(COLLECTION, {'_id': ObjectId(nation_id)})
        if not nation:
            api.abort(404, "Nation not found")
        return {'id': nation_id, NAME: nation[NAME]}

    @api.expect(nation_model)
    @api.doc('update_nation')
    def put(self, nation_id):
        try:
            update(nation_id, request.json)
            nation = dbc.read_one(COLLECTION, {'_id': ObjectId(nation_id)})
            return {'id': nation_id, NAME: nation[NAME]}
        except KeyError:
            api.abort(404, "Nation not found")

    @api.doc('delete_nation')
    def delete(self, nation_id):
        try:
            delete(nation_id)
            return '', 204
        except KeyError:
            api.abort(404, "Nation not found")

