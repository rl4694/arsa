from flask import request
from flask_restx import Resource, Namespace, fields
import os
import json

NAME = 'name'
DISASTER_TYPE = 'type'
DATE = 'date'
LOCATION = 'location'
DESCRIPTION = 'description'
DISASTERS_FILE = 'natural_disasters.json'

if os.path.exists(DISASTERS_FILE):
  with open(DISASTERS_FILE, 'r') as f:
    disasters = json.load(f)
else:
  disasters = {}


def save():
  with open(DISASTERS_FILE, 'w') as f:
    json.dump(disasters, f, indent=2)


def create(fields: dict) -> str:
  _id = str(len(disasters) + 1)
  disasters[_id] = {
    NAME: fields.get(NAME),
    DISASTER_TYPE: fields.get(DISASTER_TYPE),
    DATE: fields.get(DATE),
    LOCATION: fields.get(LOCATION),
    DESCRIPTION: fields.get(DESCRIPTION, '')
  }
  save()
  return _id


def read() -> dict:
  return disasters


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
  def get(self):
    return {'disasters': read()}

  @api.expect(disaster_model)
  def post(self):
    data = request.json
    disaster_id = create(data)
    return {'id': disaster_id, **data}, 201


@api.route('/<string:disaster_id>')
class Disaster(Resource):
  def get(self, disaster_id):
    disaster = disasters.get(disaster_id)
    if not disaster:
      api.abort(404, "Disaster not found")
    return {'id': disaster_id, **disaster}

  @api.expect(disaster_model)
  def put(self, disaster_id):
    if disaster_id not in disasters:
      api.abort(404, "Disaster not found")
    update(disaster_id, request.json)
    return {'id': disaster_id, **disasters[disaster_id]}

  def delete(self, disaster_id):
    if disaster_id not in disasters:
      api.abort(404, "Disaster not found")
    delete(disaster_id)
    return '', 204
