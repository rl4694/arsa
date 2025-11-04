from flask import request
from flask_restx import Resource, Namespace, fields
from server.db import db

NAME = 'name'
NATION = 'nation'


def is_valid_id(_id: str) -> bool:
    if isinstance(_id, str) and _id.isdigit() and int(_id) > 0:
        return True
    try:
        from bson.objectid import ObjectId
        ObjectId(_id)
        return True
    except Exception:
        return False


def length():
    return db.states.count_documents({})


def create(fields: dict, recursive=True) -> str:
    if not isinstance(fields, dict):
        raise ValueError(f'Bad type for fields: {type(fields)}')
    if not fields.get(NAME):
        raise ValueError(f'Name missing in fields: {fields.get(NAME)}')

    state_name = fields[NAME].strip().lower()
    existing_state = db.states.find_one({NAME: {"$regex": f"^{state_name}$", "$options": "i"}})

    if existing_state:
        if recursive:
            return str(existing_state['_id'])
        else:
            raise ValueError("Duplicate state detected and recursive not allowed.")

    result = db.states.insert_one({
        NAME: state_name,
        NATION: fields.get(NATION)
    })
    return str(result.inserted_id)


def read() -> dict:
    states_list = list(db.states.find())
    return {str(state['_id']): {NAME: state[NAME], NATION: state.get(NATION)} for state in states_list}


def update(state_id: str, data: dict):
    from bson.objectid import ObjectId
    result = db.states.update_one(
        {'_id': ObjectId(state_id)},
        {'$set': {NAME: data.get(NAME), NATION: data.get(NATION)}}
    )
    if result.matched_count == 0:
        raise KeyError("State not found")


def delete(state_id: str):
    from bson.objectid import ObjectId
    result = db.states.delete_one({'_id': ObjectId(state_id)})
    if result.deleted_count == 0:
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
        data = request.json
        recursive = data.get('recursive', True)
        state_id = create(data, recursive=recursive)
        return {'id': state_id, **data}, 201


@api.route('/')
class State(Resource):
    @api.doc('get_state')
    def get(self, state_id):
        from bson.objectid import ObjectId
        state = db.states.find_one({'_id': ObjectId(state_id)})
        if not state:
            api.abort(404, "State not found")
        return {'id': state_id, **state}

    @api.expect(state_model)
    @api.doc('update_state')
    def put(self, state_id):
        try:
            update(state_id, request.json)
            state = db.states.find_one({'_id': ObjectId(state_id)})
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
