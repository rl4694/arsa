"""
This file implements CRUD operations for nations.
"""

from flask import request
from flask_restx import Resource, Namespace, fields
from server.controllers.crud import CRUD
import pycountry

NATIONS_RESP = 'nations'
COLLECTION = 'nations'
NAME = 'name'
CODE = 'code'
KEY = (CODE,)

nations = CRUD(
    COLLECTION,
    KEY,
    {
        CODE: str,
        NAME: str,
    }
)


api = Namespace('nations', description='Nations CRUD operations')

nation_model = api.model('Nation', {
    CODE: fields.String(required=True, description='Nation Code'),
    NAME: fields.String(required=True, description='Nation Name'),
})


# NATIONS ENDPOINTS
@api.route('/')
class NationList(Resource):
    @api.doc('list_nations')
    def get(self):
        return {NATIONS_RESP: nations.read()}

    @api.expect(nation_model)
    @api.doc('create_nation')
    def post(self):
        data = request.json
        
        try:
            country = pycountry.countries.get(name=data['name'])
            code = country.alpha_2
        except:
            api.abort(400, f"Invalid nation name: {data['name']}")

        data['code'] = code
        data['_id'] = code
        
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
            payload = request.json
            if 'name' in payload:
                try:
                    country = pycountry.countries.get(name=payload['name'])
                    payload['code'] = country.alpha_2
                    
                except:
                    api.abort(400, f"Invalid nation name: {payload['name']}")
                    nations.delete(nation_id)
                    new_id = nations.create(payload, recursive=False)
                    record = nations.select(new_id)
                    return {NATIONS_RESP: record}

            nations.update(nation_id, payload)
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
