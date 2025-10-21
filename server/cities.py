MIN_ID_LEN = 1
NAME = 'name'
STATE = 'state'
NATION = 'nation'

cities = {}


def is_valid_id(_id: str) -> bool:
    """Return True if _id is a non-empty string."""
    if not isinstance(_id, str):
        return False
    if len(_id) < MIN_ID_LEN:
        return False
    return True


def length():
    """Return the number of cities stored."""
    return len(cities)


def create(fields: dict) -> str:
    """
    Create a new city record.
    Requires a dict with a 'name' key.
    Optional fields: state, nation
    Returns a string id.
    """
    if not isinstance(fields, dict):
        raise ValueError(f'Bad type for fields: {type(fields)}')
    if not fields.get(NAME):
        raise ValueError(f'Name missing in fields: {fields.get(NAME)}')

    # Pre-pending underscore because id is a built-in Python function
    _id = str(len(cities) + 1)
    # Currently state and nation are optional for testing,
    # Will implement proper ID in fields later with creation logic
    cities[_id] = {
        NAME: fields[NAME],
        STATE: fields.get(STATE),
        NATION: fields.get(NATION)
    }
    return _id


def read() -> dict:
    """Return all cities stored."""
    return cities


def update(city_id: str, data: dict):
    if city_id not in cities:
        raise KeyError("City not found")
    cities[city_id] = {
        NAME: data.get(NAME),
        STATE: data.get(STATE),
        NATION: data.get(NATION)
}


def delete(city_id: str):
    if city_id not in cities:
        raise KeyError("City not found")
    del cities[city_id]


from flask import request
from flask_restx import Resource, Namespace, fields

api = Namespace('cities', description='Cities CRUD operations')

city_model = api.model('City', {
    'name': fields.String(required=True, description='City Name'),
    'state': fields.String(description='State Name'),
    'nation': fields.String(description='Nation Name')
})


# CITIES ENDPOINTS
@api.route('/')
class CityList(Resource):
    @api.doc('list_cities')
    def get(self):
        return {'cities': read()}

    @api.expect(city_model)
    @api.doc('create_city')
    def post(self):
        data = request.json
        city_id = create(data)
        return {'id': city_id, **data}, 201


@api.route('/<string:city_id>')
class City(Resource):
    @api.doc('get_city')
    def get(self, city_id):
        city = cities.get(city_id)
        if not city:
            api.abort(404, "City not found")
        return {'id': city_id, **city}

    @api.expect(city_model)
    @api.doc('update_city')
    def put(self, city_id):
        try:
            update(city_id, request.json)
            return {'id': city_id, **cities[city_id]}
        except KeyError:
            api.abort(404, "City not found")

    @api.doc('delete_city')
    def delete(self, city_id):
        try:
            delete(city_id)
            return '', 204
        except KeyError:
            api.abort(404, "City not found")
