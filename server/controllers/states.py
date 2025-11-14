from flask import request
from flask_restx import Resource, Namespace, fields
from bson.objectid import ObjectId
import server.common as common
import data.db_connect as dbc

COLLECTION = 'states'
NAME = 'name'
NATION = 'nation'


def length():
    return len(dbc.read(COLLECTION, no_id=False))


def create(fields: dict, recursive=True) -> str:
    if not isinstance(fields, dict):
        raise ValueError(f'Bad type for fields: {type(fields)}')
    if not fields.get(NAME):
        raise ValueError(f'Name missing in fields: {fields.get(NAME)}')

    state_name = fields[NAME].strip().lower()
    existing_state = dbc.read_one(COLLECTION, {NAME: {"$regex": f"^{state_name}$", "$options": "i"}})

    if existing_state:
        if recursive:
            return str(existing_state['_id'])
        else:
            raise ValueError("Duplicate state detected and recursive not allowed.")

    result = dbc.create(COLLECTION, {
        NAME: state_name,
        NATION: fields.get(NATION)
    })
    if not result or not getattr(result, "inserted_id", None):
        raise RuntimeError("Create failed: no inserted_id")
    return str(result.inserted_id)


def read() -> dict:
    states_list = dbc.read(COLLECTION, no_id=False)
    return {str(state['_id']): {NAME: state[NAME], NATION: state.get(NATION)} for state in states_list}


def update(state_id: str, data: dict):
    result = dbc.update(COLLECTION, {'_id': ObjectId(state_id)}, {
        NAME: data.get(NAME),
        NATION: data.get(NATION)
    })
    if not result or getattr(result, "matched_count", 0) == 0:
        raise KeyError("State not found")


def delete(state_id: str):
    deleted_count = dbc.delete(COLLECTION, {'_id': ObjectId(state_id)})
    if deleted_count == 0:
        raise KeyError("State not found")


api = Namespace('states', description='States CRUD operations')

state_model = api.model('State', {
    'name': fields.String(required=True, description='State Name'),
    'nation': fields.String(description='Nation Name')
})


@api.route('/')
class StateList(Resource):
    @api.doc('list_states')
    def get(self):
        return {'states': read()}

    @api.expect(state_model)
    @api.doc('create_state')
    def post(self):
        data = request.json or {}
        recursive = data.get('recursive', True)
        state_id = create(data, recursive=recursive)
        return {'id': state_id, **data}, 201


@api.route('/<string:state_id>')
class State(Resource):
    @api.doc('get_state')
    def get(self, state_id):
        if not common.is_valid_id(state_id):
            api.abort(404, "State not found")
        state = dbc.read_one(COLLECTION, {'_id': ObjectId(state_id)})
        if not state:
            api.abort(404, "State not found")
        return {'id': state_id, NAME: state[NAME], NATION: state.get(NATION)}


    @api.expect(state_model)
    @api.doc('update_state')
    def put(self, state_id):
        try:
            update(state_id, request.json)
            state = dbc.read_one(COLLECTION, {'_id': ObjectId(state_id)})
            return {'id': state_id, **state}
        except KeyError:
            api.abort(404, "State not found")

    @api.doc('delete_state')
    def delete(self, state_id):
        try:
            delete(state_id)
            return '', 204
        except KeyError:
            api.abort(404, "State not found")
