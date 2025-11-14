"""
This file implements CRUD operations for nations.
"""

from flask import request
from flask_restx import Resource, Namespace, fields
from bson.objectid import ObjectId
import data.db_connect as dbc

COLLECTION = 'nations'
NAME = 'name'


# Return the number of nations currently stored.
def length():
    return len(dbc.read(COLLECTION, no_id=False))

# Create a new nation record and return its id.
def create(fields: dict, recursive=True) -> str:
    if not isinstance(fields, dict):
        raise ValueError(f'Bad type for fields: {type(fields)}')
    if not fields.get(NAME):
        raise ValueError(f'Name missing in fields: {fields.get(NAME)}')

    # Duplicate check (normalize to lower case and trim whitespace)
    nation_name = fields[NAME].strip().lower()
    existing = dbc.read_one(COLLECTION, {NAME: {"$regex": f"^{nation_name}$", "$options": "i"}})
    if existing:
        if recursive:
            return str(existing['_id'])
        else:
            raise ValueError("Duplicate nation detected and recursive not allowed.")

    result = dbc.create(COLLECTION, {NAME: nation_name})
    return str(result.inserted_id)

# Return the nations store as a dictionary.
def read() -> dict:
    items = dbc.read(COLLECTION, no_id=False)
    return {str(nation['_id']): {NAME: nation[NAME]} for nation in items}

# Update an existing nation's data.
# Raises: KeyError: if the nation id does not exist.
def update(nation_id: str, data: dict):
    result = dbc.update(COLLECTION, {'_id': ObjectId(nation_id)}, {NAME: data.get(NAME)})
    if result.matched_count == 0:
        raise KeyError("Nation not found")

# Delete a nation by id.
def delete(nation_id: str):
    deleted_count = dbc.delete(COLLECTION, {'_id': ObjectId(nation_id)})
    if deleted_count == 0:
        raise KeyError("Nation not found")


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

