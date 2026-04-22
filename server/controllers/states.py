"""
This file implements CRUD operations for states.
"""

from flask import request
from flask_restx import Resource, Namespace, fields
import server.controllers.crud as crud
import pycountry
import security.security as security

SECURITY_FEATURE = security.STATES
STATES_RESP = 'records'
COLLECTION = 'states'
NAME = 'name'
NATION_NAME = 'nation_name'
KEY = (NAME, NATION_NAME)

states = crud.CRUD(
    COLLECTION,
    KEY,
    {
        NAME: str,
        NATION_NAME: str,
    }
)

api = Namespace('states', description='States CRUD operations')

state_model = api.model('State', {
    NAME: fields.String(required=True, description='State Name'),
    NATION_NAME: fields.String(required=True, description='Nation Code'),
})

@api.route('/', strict_slashes=False)
class StateList(Resource):
    """
    Collection-level operations for states.
    Provides list and create functionality.
    """
    @security.require_auth(SECURITY_FEATURE, security.READ)
    @api.doc('list_states')
    def get(self):
        """Return all states."""
        return {STATES_RESP: states.read()}

    @security.require_auth(SECURITY_FEATURE, security.CREATE)
    @api.expect(state_model)
    @api.doc('create_state')
    def post(self):
        """Create a new state."""
        data = request.json or {}
        # data['nation_code'] = data['nation_code'].upper()
        # try:
        #     subs = pycountry.subdivisions.get(country_code=data['nation_code'].upper())
        #     match = [s for s in subs if s.name.lower() == data['name'].lower()][0]
        #     state_code = match.code.split('-')[1]
        # except:
        #     api.abort(400, f"Invalid state or nation: {data}")

        # data['code'] = state_code
        # data['state_id'] = f"{data['nation_code']}-{state_code}"
        _id = states.create(data)
        created = states.select(_id)
        return {STATES_RESP: created}, 201


@api.route('/fields')
class StateFields(Resource):
    @security.require_auth(SECURITY_FEATURE, security.READ)
    @api.doc('get_fields')
    def get(self):
        """Get field information for states."""
        return [
            { crud.ATTRIBUTE: NAME, crud.DISPLAY: "City Name", crud.TYPE: "text" },
            { crud.ATTRIBUTE: NATION_NAME, crud.DISPLAY: "Nation Name", crud.TYPE: "text" },
        ]


@api.route('/<string:state_id>')
class State(Resource):
    """
    Item-level operations for a single state.
    Provides retrieve, update, and delete functionality.
    """
    @security.require_auth(SECURITY_FEATURE, security.READ)
    @api.doc('get_state')
    def get(self, state_id):
        """Retrieve a single state by ID."""
        record = states.select(state_id)
        return {STATES_RESP: record}

    @security.require_auth(SECURITY_FEATURE, security.UPDATE)
    @api.expect(state_model)
    @api.doc('update_state')
    def put(self, state_id):
        """Update a state by ID."""
        payload = request.json or {}
        # if 'name' in payload or 'nation_code' in payload:
        #     try:
        #         state = states.select(state_id)
        #         subs = pycountry.subdivisions.get(
        #             country_code=(payload.get("nation_code") or state["nation_code"] or "").upper() or None
        #         )
        #         state_name = payload.get("name") or state["name"]
        #         match = next(s for s in subs if s.name.casefold() == state_name.casefold())
        #         new_code = match.code.split('-')[1]
        #     except:
        #         api.abort(400, "Invalid state or nation in update")

        #     new_payload = {**states.select(state_id), **payload}
        #     new_payload['code'] = new_code
        #     new_payload['state_id'] = f"{new_payload['nation_code']}-{new_code}"

        #     states.delete(state_id)
        #     new_id = states.create(new_payload)
        #     record = states.select(new_id)
        #     return {STATES_RESP: record}

        states.update(state_id, request.json)
        record = states.select(state_id)
        return {STATES_RESP: record}

    @security.require_auth(SECURITY_FEATURE, security.DELETE)
    @api.doc('delete_state')
    def delete(self, state_id):
        """Delete a state by ID."""
        states.delete(state_id)
        return '', 204
