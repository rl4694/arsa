from flask import request
from flask_restx import Resource, Namespace, fields
from server.db import db

NAME = 'name'
STATE = 'state'
NATION = 'nation'


def create(fields: dict, recursive=True) -> str:
    if not isinstance(fields, dict):
        raise ValueError(f'Bad type for fields: {type(fields)}')
    if not fields.get(NAME):
        raise ValueError(f'Name missing in fields: {fields.get(NAME)}')

    city_name = fields[NAME].strip().lower()
    existing_city = db.cities.find_one({NAME: {"$regex": f"^{city_name}$", "$options": "i"}})

    if existing_city:
        if recursive:
            return str(existing_city['_id'])
        else:
            raise ValueError("Duplicate city detected and recursive not allowed.")

    result = db.cities.insert_one({
        NAME: city_name,
        STATE: fields.get(STATE),
        NATION: fields.get(NATION)
    })
    return str(result.inserted_id)


def read() -> dict:
    cities_list = list(db.cities.find())
    return {str(city['_id']): {NAME: city[name], STATE: city.get(STATE), NATION: city.get(NATION)} for city in cities_list}


def update(city_id: str, data: dict):
    from bson.objectid import ObjectId
    result = db.cities.update_one(
        {'_id': ObjectId(city_id)},
        {'$set': {NAME: data.get(NAME), STATE: data.get(STATE), NATION: data.get(NATION)}}
    )
    if result.matched_count == 0:
        raise KeyError("City not found")


def delete(city_id: str):
    from bson.objectid import ObjectId
    result = db.cities.delete_one({'_id': ObjectId(city_id)})
    if result.deleted_count == 0:
        raise KeyError("City not found")


api = Namespace('cities', description='Cities CRUD operations')

city_model = api.model('City', {
    'name': fields.String(required=True, description='City Name'),
    'state': fields.String(description='State Name'),
    'nation': fields.String(description='Nation Name')
})


@api.route('/')
class CityList(Resource):
    @api.doc('list_cities')
    def get(self):
        return {'cities': read()}

    @api.expect(city_model)
    @api.doc('create_city')
    def post(self):
        data = request.json
        recursive = data.get('recursive', True)
        city_id = create(data, recursive=recursive)
        return {'id': city_id, **data}, 201


@api.route('/')
class City(Resource):
    @api.doc('get_city')
    def get(self, city_id):
        from bson.objectid import ObjectId
        city = db.cities.find_one({'_id': ObjectId(city_id)})
        if not city:
            api.abort(404, "City not found")
        return {'id': city_id, **city}

    @api.expect(city_model)
    @api.doc('update_city')
    def put(self, city_id):
        try:
            update(city_id, request.json)
            city = db.cities.find_one({'_id': ObjectId(city_id)})
            return {'id': city_id, **city}
        except KeyError:
            api.abort(404, "City not found")

    @api.doc('delete_city')
    def delete(self, city_id):
        try:
            delete(city_id)
            return '', 204
        except KeyError:
            api.abort(404, "City not found")
