# server/nations.py
from flask import request
from flask_restx import Resource, Namespace, fields
import os
import json


MIN_ID_LEN = 1
NAME = 'name'
NATIONS_FILE = 'json/nations.json'

nations = {}

# Return True when `_id` is a valid non-empty string id.
def is_valid_id(_id: str) -> bool:
    if not isinstance(_id, str):
        return False
    if len(_id) < MIN_ID_LEN:
        return False
    return True

# Return the number of nations currently stored.
def length():
    return len(nations)

# Create a new nation record and return its id.
def create(fields: dict, recursive=True) -> str:
    if not isinstance(fields, dict):
        raise ValueError(f'Bad type for fields: {type(fields)}')
    if not fields.get(NAME):
        raise ValueError(f'Name missing in fields: {fields.get(NAME)}')

    # Duplicate check (normalize to lower case and trim whitespace)
    nation_name = fields[NAME].strip().lower()
    for _id, nation in nations.items():
        if nation.get(NAME, '').strip().lower() == nation_name:
            if recursive:
                return _id
            else:
                raise ValueError("Duplicate nation detected and recursive not allowed.")

    # Pre-pending underscore because id is a built-in Python function
    _id = str(len(nations) + 1)
    nations[_id] = {
        # Standardize Lower case
        NAME: nation_name
    }
    return _id

# Return the nations store as a dictionary.
def read() -> dict:
    return nations

# Update an existing nation's data.
# Raises: KeyError: if the nation id does not exist.
def update(nation_id: str, data: dict):
    if nation_id not in nations:
        raise KeyError("Nation not found")
    nations[nation_id] = {
        NAME: data.get(NAME)
    }

# Delete a nation by id.
def delete(nation_id: str):
    if nation_id not in nations:
        raise KeyError("Nation not found")
    del nations[nation_id]


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
        nation = nations.get(nation_id)
        if not nation:
            api.abort(404, "Nation not found")
        return {'id': nation_id, **nation}

    @api.expect(nation_model)
    @api.doc('update_nation')
    def put(self, nation_id):
        try:
            update(nation_id, request.json)
            return {'id': nation_id, **nations[nation_id]}
        except KeyError:
            api.abort(404, "Nation not found")

    @api.doc('delete_nation')
    def delete(self, nation_id):
        try:
            delete(nation_id)
            return '', 204
        except KeyError:
            api.abort(404, "Nation not found")

