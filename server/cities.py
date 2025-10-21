from flask import Flask, request
from flask_restx import Resource, Api, fields # Namespace

MIN_ID_LEN = 1
NAME = 'name'
STATE = 'state'
NATION = 'nation'

CITIES_EP = '/cities'
CITIES_RESP = 'cities'

cities = {}

city_model = api.model(
    'City',
    {
        'name': fields.String(required=True, description='City Name')
    }
)

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


# CITIES ENDPOINTS
@api.route(CITIES_EP)
class CityList(Resource):
    @api.doc('list_cities')
    def get(self):
        cities = ct.read()
        return {
            CITIES_RESP: cities,
        }

    @api.expect(city_model)
    @api.doc('create_city')
    def post(self):
        data = request.json
        city_id = ct.create(data)
        return {'id': city_id, **data}, 201


@api.route('/cities/<string:city_id>')
class City(Resource):
    @api.doc('get_city')
    def get(self, city_id):
        city = ct.cities.get(city_id)
        if not city:
            api.abort(404, "City not found")
        return {'id': city_id, **city}

    @api.expect(city_model)
    @api.doc('update_city')
    def put(self, city_id):
        if city_id not in ct.cities:
            api.abort(404, "City not found")
        data = request.json
        ct.cities[city_id] = data
        return {'id': city_id, **data}

    @api.doc('delete_city')
    def delete(self, city_id):
        if city_id not in ct.cities:
            api.abort(404, "City not found")
        del ct.cities[city_id]
        return '', 204
