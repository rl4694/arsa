from flask import request
from flask_restx import Resource, Namespace, fields
from server.controllers.crud import CRUD
import pycountry

STATES_RESP = 'states'
COLLECTION = 'states'
NAME = 'name'
NATION_CODE = 'nation_code'
STATE_CODE = 'code'
STATE_ID = 'state_id'
KEY = (STATE_ID,)

states = CRUD(
    COLLECTION,
    KEY,
    {
        STATE_ID: str,
        STATE_CODE: str,
        NAME: str,
        NATION_CODE: str,
    }
)

api = Namespace('states', description='States CRUD operations')

state_model = api.model('State', {
    'name': fields.String(required=True, description='State Name'),
    'nation_code': fields.String(required=True, description='Nation Code')
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
        data['nation_code'] = data['nation_code'].upper()
        try:
            subs = pycountry.subdivisions.get(country_code=data['nation_code'].upper())
            match = [s for s in subs if s.name.lower() == data['name'].lower()][0]
            state_code = match.code.split('-')[1]
        except:
            api.abort(400, f"Invalid state or nation: {data}")

        data['code'] = state_code
        data['state_id'] = f"{data['nation_code']}-{state_code}"
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
        payload = request.json or {}
        if 'name' in payload or 'nation_code' in payload:
            try:
                state = states.select(state_id)
                subs = pycountry.subdivisions.get(
                    country_code=(payload.get("nation_code") or state["nation_code"] or "").upper() or None
                )
                state_name = payload.get("name") or state["name"]
                match = next(s for s in subs if s.name.casefold() == state_name.casefold())
                new_code = match.code.split('-')[1]
            except:
                api.abort(400, "Invalid state or nation in update")

            new_payload = {**states.select(state_id), **payload}
            new_payload['code'] = new_code
            new_payload['nation_code'] = new_payload['nation_code'].upper()
            new_payload['state_id'] = f"{new_payload['nation_code']}-{new_code}"

            states.delete(state_id)
            new_id = states.create(new_payload, recursive=False)
            record = states.select(new_id)
            return {STATES_RESP: record}

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
