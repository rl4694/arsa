"""
This file implements CRUD operations for nations.
"""

from flask import request
from flask_restx import Resource, Namespace, fields
from server.controllers.crud import CRUD

NATIONS_RESP = 'nations'
COLLECTION = 'nations'
NAME = 'name'
KEY = (NAME,)

nations = CRUD(
    COLLECTION,
    KEY,
    {
        NAME: str,
    }
)


api = Namespace('nations', description='Nations CRUD operations')

nation_model = api.model('Nation', {
    'name': fields.String(required=True, description='Nation Name')
})


# NATIONS ENDPOINTS
@api.route('/')
class NationList(Resource):
    @api.doc('list_nations')
    def get(self):
        records = nations.read()
        return {NATIONS_RESP: list(records.values())}

    @api.expect(nation_model)
    @api.doc('create_nation')
    def post(self):
        data = request.json
        _id = nations.create(data, recursive=False)
        created = nations.select(_id)
        return {NATIONS_RESP: created}, 201


@api.route('/<string:nation_id>')
class Nation(Resource):
    @api.doc('get_nation')
    def get(self, nation_id):
        try:
            record = nations.select(nation_id)
            return {NATIONS_RESP: record}
        except:
            api.abort(404, "Nation not found")

    @api.expect(nation_model)
    @api.doc('update_nation')
    def put(self, nation_id):
        try:
            nations.update(nation_id, request.json)
            record = nations.select(nation_id)
            return {NATIONS_RESP: record}
        except KeyError:
            api.abort(404, "Nation not found")

    @api.doc('delete_nation')
    def delete(self, nation_id):
        try:
            nations.delete(nation_id)
            return '', 204
        except KeyError:
            api.abort(404, "Nation not found")

