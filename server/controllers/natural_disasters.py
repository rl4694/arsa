from flask import request
from flask_restx import Resource, Namespace, fields
import data.db_connect as dbc

NAME = 'name'
DISASTER_TYPE = 'type'
DATE = 'date'
LOCATION = 'location'
DESCRIPTION = 'description'

NATURAL_DISASTERS_COLLECTION = 'natural_disasters'


def is_valid_id(_id: str) -> bool:
    """Validate if an ID is valid (ObjectId format)."""
    if isinstance(_id, str) and _id.isdigit() and int(_id) > 0:
        return True
    try:
        from bson.objectid import ObjectId
        ObjectId(_id)
        return True
    except Exception:
        return False


@dbc.needs_db
def length():
    """Return the count of disasters in the database."""
    return dbc.client[dbc.SE_DB][NATURAL_DISASTERS_COLLECTION].count_documents({})


def create(fields: dict) -> str:
    """Create a new natural disaster record and return its ID."""
    if not isinstance(fields, dict):
        raise ValueError(f'Bad type for fields: {type(fields)}')
    if not fields.get(NAME):
        raise ValueError(f'Name missing in fields: {fields.get(NAME)}')
    
    doc = {
        NAME: fields.get(NAME),
        DISASTER_TYPE: fields.get(DISASTER_TYPE),
        DATE: fields.get(DATE),
        LOCATION: fields.get(LOCATION),
        DESCRIPTION: fields.get(DESCRIPTION, '')
    }
    # @needs_db decorator in dbc.create ensures connection
    result = dbc.create(NATURAL_DISASTERS_COLLECTION, doc)
    return str(result.inserted_id)


def read() -> dict:
    """Return all natural disasters as a dictionary."""
    # @needs_db decorator in dbc.read ensures connection
    disasters_list = dbc.read(NATURAL_DISASTERS_COLLECTION, no_id=False)
    return {
        str(disaster['_id']): {
            NAME: disaster.get(NAME),
            DISASTER_TYPE: disaster.get(DISASTER_TYPE),
            DATE: disaster.get(DATE),
            LOCATION: disaster.get(LOCATION),
            DESCRIPTION: disaster.get(DESCRIPTION, '')
        } for disaster in disasters_list
    }


def update(disaster_id: str, data: dict):
    """Update an existing disaster's data."""
    from bson.objectid import ObjectId
    update_dict = {
        NAME: data.get(NAME),
        DISASTER_TYPE: data.get(DISASTER_TYPE),
        DATE: data.get(DATE),
        LOCATION: data.get(LOCATION),
        DESCRIPTION: data.get(DESCRIPTION, '')
    }
    # @needs_db decorator in dbc.update ensures connection
    result = dbc.update(NATURAL_DISASTERS_COLLECTION, {'_id': ObjectId(disaster_id)}, update_dict)
    if result.matched_count == 0:
        raise KeyError("Disaster not found")


def delete(disaster_id: str):
    """Delete a disaster by ID."""
    from bson.objectid import ObjectId
    # @needs_db decorator in dbc.delete ensures connection
    deleted_count = dbc.delete(NATURAL_DISASTERS_COLLECTION, {'_id': ObjectId(disaster_id)})
    if deleted_count == 0:
        raise KeyError("Disaster not found")


api = Namespace('natural_disasters', description='Natural Disasters CRUD operations')
disaster_model = api.model('NaturalDisaster', {
  'name': fields.String(required=True),
  'type': fields.String(required=True),
  'date': fields.String(required=True),
  'location': fields.String(required=True),
  'description': fields.String()
})


@api.route('/')
class DisasterList(Resource):
    @api.doc('list_disasters')
    def get(self):
        """Get all natural disasters."""
        return {'disasters': read()}

    @api.expect(disaster_model)
    @api.doc('create_disaster')
    def post(self):
        """Create a new natural disaster."""
        data = request.json
        disaster_id = create(data)
        return {'id': disaster_id, **data}, 201


@api.route('/<string:disaster_id>')
class Disaster(Resource):
    @api.doc('get_disaster')
    def get(self, disaster_id):
        """Get a specific disaster by ID."""
        from bson.objectid import ObjectId
        try:
            # @needs_db decorator in dbc.read_one ensures connection
            disaster = dbc.read_one(NATURAL_DISASTERS_COLLECTION, {'_id': ObjectId(disaster_id)})
            if not disaster:
                api.abort(404, "Disaster not found")
            # Remove _id from response, we're including it as 'id' parameter
            disaster.pop('_id', None)
            return {'id': disaster_id, **disaster}
        except Exception:
            api.abort(404, "Disaster not found")

    @api.expect(disaster_model)
    @api.doc('update_disaster')
    def put(self, disaster_id):
        """Update an existing disaster."""
        try:
            update(disaster_id, request.json)
            from bson.objectid import ObjectId
            # @needs_db decorator in dbc.read_one ensures connection
            disaster = dbc.read_one(NATURAL_DISASTERS_COLLECTION, {'_id': ObjectId(disaster_id)})
            disaster.pop('_id', None)
            return {'id': disaster_id, **disaster}
        except KeyError:
            api.abort(404, "Disaster not found")
        except Exception:
            api.abort(400, "Bad request")

    @api.doc('delete_disaster')
    def delete(self, disaster_id):
        """Delete a disaster by ID."""
        try:
            delete(disaster_id)
            return '', 204
        except KeyError:
            api.abort(404, "Disaster not found")
        except Exception:
            api.abort(400, "Bad request")
