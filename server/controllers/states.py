from flask import request
from flask_restx import Resource, Namespace, fields
from bson.objectid import ObjectId
from server.controllers.crud import CRUDController
import server.common as common
import data.db_connect as dbc

COLLECTION = 'states'
NAME = 'name'
NATION = 'nation'
KEY = (NAME, NATION)

# Use the shared CRUDController to centralize cache + DB logic.
controller = CRUDController(
    COLLECTION,
    KEY,
    required_fields=(NAME, NATION),
    normalize_fields=(NAME, NATION),
)


def length():
    return controller.length()


def create(fields: dict, recursive=True) -> str:
    return controller.create(fields, recursive=recursive)


def read() -> dict:
    return controller.read()


def get_by_name(name: str) -> dict:
    n = name.strip().lower()
    matches = {}
    for k, rec in controller.cache.read().items():
        if k[0] == n:
            matches[k] = rec
    return matches


def get_cache_stats() -> dict:
    return controller.cache.get_stats()


def update(state_id: str, fields: dict):
    return controller.update(state_id, fields)


def delete(state_id: str):
    return controller.delete(state_id)


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


@api.route('/cache/stats')
class CacheStats(Resource):
    @api.doc('get_cache_stats')
    def get(self):
        return get_cache_stats()


@api.route('/<string:state_id>')
class State(Resource):
    @api.doc('get_state')
    def get(self, state_id):
        if not common.is_valid_id(state_id):
            api.abort(404, "State not found")
        
        states = cache.read_flat()
        for state in states.values():
            if str(state.get('_id')) == state_id:
                return {'id': state_id, NAME: state[NAME], NATION: state.get(NATION)}
        
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
