"""
This file implements CRUD operations for natural disasters.
"""

from flask import request
from flask_restx import Resource, Namespace, fields
from server.controllers.crud import CRUD

DISASTERS_RESP = 'disasters'
COLLECTION = 'natural_disasters'
NAME = 'name'
DISASTER_TYPE = 'type'
DATE = 'date'
LOCATION = 'location'
DESCRIPTION = 'description'
KEY = (NAME, DATE, LOCATION)

disasters = CRUD(
    COLLECTION,
    KEY,
    {
        NAME: str,
        DISASTER_TYPE: str,
        DATE: str,
        LOCATION: str,
        DESCRIPTION: str,
    }
)


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
        return {DISASTERS_RESP: disasters.read()}

    @api.expect(disaster_model)
    @api.doc('create_disaster')
    def post(self):
        """Create a new natural disaster."""
        data = request.json
        _id = disasters.create(data)
        created = disasters.select(_id)
        return {DISASTERS_RESP: created}, 201


@api.route('/<string:disaster_id>')
class Disaster(Resource):
    @api.doc('get_disaster')
    def get(self, disaster_id):
        """Get a specific disaster by ID."""
        try:
            record = disasters.select(disaster_id)
            return {DISASTERS_RESP: record}
        except Exception:
            api.abort(404, "Disaster not found")

    @api.expect(disaster_model)
    @api.doc('update_disaster')
    def put(self, disaster_id):
        """Update an existing disaster."""
        try:
            disasters.update(disaster_id, request.json)
            record = disasters.select(disaster_id)
            return {DISASTERS_RESP: record}
        except KeyError:
            api.abort(404, "Disaster not found")
        except Exception:
            api.abort(400, "Bad request")

    @api.doc('delete_disaster')
    def delete(self, disaster_id):
        """Delete a disaster by ID."""
        try:
            disasters.delete(disaster_id)
            return '', 204
        except KeyError:
            api.abort(404, "Disaster not found")
        except Exception:
            api.abort(400, "Bad request")
