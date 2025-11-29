from flask import request
from flask_restx import Resource, Namespace, fields
from bson.objectid import ObjectId
from server.controllers.crud import CRUD
import server.common as common
import data.db_connect as dbc

COLLECTION = 'states'
NAME = 'name'
NATION = 'nation'
KEY = (NAME, NATION)

class States(CRUD):
    def __init__(self):
        fields = {
            NAME: str,
            NATION: str,
        }
        super(COLLECTION, KEY, fields)

# Use the shared Crud to centralize cache + DB logic.
# controller = CRUD(
#     COLLECTION,
#     KEY,
#     required_fields=(NAME, NATION),
#     normalize_fields=(NAME, NATION),
# )


# def length():
#     return controller.length()


# def create(fields: dict, recursive=True) -> str:
#     return controller.create(fields, recursive=recursive)


# def read() -> dict:
#     return controller.read()


# def get_by_name(name: str) -> dict:
#     n = name.strip().lower()
#     matches = {}
#     for k, rec in controller.cache.read().items():
#         if k[0] == n:
#             matches[k] = rec
#     return matches


# def update(key_or_id, fields: dict):
#     """Support either tuple-key updates (name,nation) used by tests,
#     or id-string updates used by the HTTP endpoints.
#     """
#     # key tuple path
#     if isinstance(key_or_id, tuple):
#         key = key_or_id
#         if not isinstance(fields, dict):
#             raise ValueError(f'Bad type for fields: {type(fields)}')
#         if not isinstance(key, tuple) or len(key) < len(KEY):
#             raise ValueError(f'Key must be a tuple of length {len(KEY)}: {key}')

#         result = dbc.update(COLLECTION, {NAME: key[0], NATION: key[1]}, fields)
#         if result.matched_count == 0:
#             raise KeyError("State not found")
#         controller.cache.reload()
#         return

#     # id-string path
#     if isinstance(key_or_id, str):
#         return controller.update(key_or_id, fields)

#     raise ValueError('First argument must be a key tuple or id string')


# def delete(key_or_id):
#     """Delete by key tuple or by id string."""
#     if isinstance(key_or_id, tuple):
#         key = key_or_id
#         if not isinstance(key, tuple) or len(key) < len(KEY):
#             raise ValueError(f'Key must be a tuple of length {len(KEY)}: {key}')

#         deleted_count = dbc.delete(COLLECTION, {NAME: key[0], NATION: key[1]})
#         if deleted_count == 0:
#             raise KeyError("State not found")
#         controller.cache.reload()
#         return

#     if isinstance(key_or_id, str):
#         return controller.delete(key_or_id)

#     raise ValueError('Argument must be a key tuple or id string')


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
        state = controller.read_one_by_id(state_id)
        return {'id': state_id, NAME: state[NAME], NATION: state.get(NATION)}, 201


@api.route('/<string:state_id>')
class State(Resource):
    @api.doc('get_state')
    def get(self, state_id):
        if not common.is_valid_id(state_id):
            api.abort(404, "State not found")
        state = controller.read_one_by_id(state_id)
        if not state:
            api.abort(404, "State not found")
        return {'id': state_id, NAME: state[NAME], NATION: state.get(NATION)}


    @api.expect(state_model)
    @api.doc('update_state')
    def put(self, state_id):
        try:
            update(state_id, request.json)
            state = controller.read_one_by_id(state_id)
            return {'id': state_id, NAME: state[NAME], NATION: state.get(NATION)}
        except KeyError:
            api.abort(404, "State not found")

    @api.doc('delete_state')
    def delete(self, state_id):
        try:
            delete(state_id)
            return '', 204
        except KeyError:
            api.abort(404, "State not found")
