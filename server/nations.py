# server/nations.py
from flask import request
from flask_restx import Resource, Namespace, fields

import os
import json

MIN_ID_LEN = 1
NAME = 'name'

NATIONS_FILE = 'nations.json'

# Load nations from predefined file if exists, else load the local
if os.path.exists(NATIONS_FILE):
    with open(NATIONS_FILE, 'r') as f:
        nations = json.load(f)
else:
    nations = {}


def is_valid_id(_id: str) -> bool:
    if not isinstance(_id, str):
        return False
    if len(_id) < MIN_ID_LEN:
        return False
    return True


def length():
    return len(nations)


# Save nations to predefined file
def save():
    """Save current nations to file."""
    os.makedirs(os.path.dirname(NATIONS_FILE) or '.', exist_ok=True)
    with open(NATIONS_FILE, 'w') as f:
        json.dump(nations, f, indent=2)


def create(fields: dict) -> str:
    if not isinstance(fields, dict):
        raise ValueError(f'Bad type for fields: {type(fields)}')
    if not fields.get(NAME):
        raise ValueError(f'Name missing in fields: {fields.get(NAME)}')
    # Duplicate check
    nation_name = fields[NAME].strip().lower()
    for _id, nation in nations.items():
        if nation.get(NAME, '').strip().lower() == nation_name:
            return _id
    # Pre-pending underscore because id is a built-in Python function
    _id = str(len(nations) + 1)
    nations[_id] = {
        # Standardize Lower case
        NAME: nation_name
    }
    save()
    return _id


def read() -> dict:
    return nations


def update(nation_id: str, data: dict):
    if nation_id not in nations:
        raise KeyError("Nation not found")
    nations[nation_id] = {
        NAME: data.get(NAME)
    }
    save()


def delete(nation_id: str):
    if nation_id not in nations:
        raise KeyError("Nation not found")
    del nations[nation_id]
    save()


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
        nation_id = create(data)
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
