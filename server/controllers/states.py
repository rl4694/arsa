from flask import request
from flask_restx import Resource, Namespace, fields
from server.controllers.crud import CRUD

STATES_RESP = 'states'
COLLECTION = 'states'
NAME = 'name'
NATION = 'nation'
KEY = (NAME, NATION)

states = CRUD(
    COLLECTION,
    KEY,
    {
        NAME: str,
        NATION: str,
    }
)


api = Namespace('states', description='States CRUD operations')

state_model = api.model('State', {
    'name': fields.String(required=True, description='State Name'),
    'nation': fields.String(description='Nation Name')
})


@api.route('/')
class StateList(Resource):
    @api.doc('list_states')
    def get(self):
        records = states.read()
        return {STATES_RESP: list(records.values())}

    @api.expect(state_model)
    @api.doc('create_state')
    def post(self):
        data = request.json or {}
        _id = states.create(data, recursive=False)
        created = states.select(_id)
        return {STATES_RESP: created}, 201


@api.route('/<string:state_id>')
class State(Resource):
    @api.doc('get_state')
    def get(self, state_id):
        try:
            record = states.select(state_id)
            return {STATES_RESP: record}
        except:
            api.abort(404, "State not found")

    @api.expect(state_model)
    @api.doc('update_state')
    def put(self, state_id):
        try:
            states.update(state_id, request.json)
            record = states.select(state_id)
            return {STATES_RESP: record}
        except KeyError:
            api.abort(404, "State not found")

    @api.doc('delete_state')
    def delete(self, state_id):
        try:
            states.delete(state_id)
            return '', 204
        except KeyError:
            api.abort(404, "State not found")
