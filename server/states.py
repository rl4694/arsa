# server/states.py
from flask import request
from flask_restx import Resource, Namespace, fields

MIN_ID_LEN = 1
NAME = 'name'
NATION = 'nation'

import os
import json

STATES_FILE = 'states.json'

# Load states from predefined file if exists, else load empty
if os.path.exists(STATES_FILE):
    with open(STATES_FILE, 'r') as f:
        states = json.load(f)
else:
    states = {}


def is_valid_id(_id: str) -> bool:
    """Return True if _id is a non-empty string."""
    if not isinstance(_id, str):
        return False
    if len(_id) < MIN_ID_LEN:
        return False
    return True


def length() -> int:
    """Return the number of states stored."""
    return len(states)
    
    
def save():
    """Save current states to file."""
    os.makedirs(os.path.dirname(STATES_FILE) or '.', exist_ok=True)
    with open(STATES_FILE, 'w') as f:
        json.dump(states, f, indent=2)


def create(fields: dict) -> str:
    """
    Create a new state record.
    Requires a dict with a 'name' key.
    Returns a string id.
    """
    if not isinstance(fields, dict):
        raise ValueError(f'Bad type for fields: {type(fields)}')
    if not fields.get(NAME):
        raise ValueError(f'Name missing in fields: {fields.get(NAME)}')
    # Check for duplicates
    state_name = fields[NAME].strip().lower()
    for _id, state in states.items():
        if state.get(NAME, '').strip().lower() == state_name:
            return _id
    _id = str(len(states) + 1)
    states[_id] = {
        NAME: state_name,
        NATION: fields.get(NATION)
    }
    save()
    return _id


def read() -> dict:
    return states


def update(state_id: str, data: dict):
    if state_id not in states:
        raise KeyError("State not found")
    states[state_id] = {
        NAME: data.get(NAME),
        NATION: data.get(NATION)
    }
    save()


def delete(state_id: str):
    if state_id not in states:
        raise KeyError("State not found")
    del states[state_id]
    save()


api = Namespace('states', description='States CRUD operation')

state_model = api.model('State', {
    'name': fields.String(required=True, description='State Name'),
    'nation': fields.String(description='Nation Name')
})


# STATES ENDPOINTS
@api.route('/')
class StateList(Resource):
    @api.doc('list_states')
    def get(self):
        return {'states': read()}

    @api.expect(state_model)
    @api.doc('create_state')
    def post(self):
        data = request.json
        state_id = create(data)
        return {'id': state_id, **data}, 201


@api.route('/<string:state_id>')
class State(Resource):
    @api.doc('get_state')
    def get(self, state_id):
        state = states.get(state_id)
        if not state:
            api.abort(404, "State not found")
        return {'id': state_id, **state}

    @api.expect(state_model)
    @api.doc('update_state')
    def put(self, state_id):
        try:
            update(state_id, request.json)
            return {'id': state_id, **states[state_id]}
        except KeyError:
            api.abort(404, "State not found")

    @api.doc('delete_state')
    def delete(self, state_id):
        try:
            delete(state_id)
            return '', 204
        except KeyError:
            api.abort(404, "State not found")
