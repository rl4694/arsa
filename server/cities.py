# server/cities.py
import os
import json
from server import states

MIN_ID_LEN = 1
NAME = 'name'
STATE = 'state'
NATION = 'nation'

CITIES_FILE = 'cities.json'

# Load cities from predefined file if exists, else load the local
if os.path.exists(CITIES_FILE):
    with open(CITIES_FILE, 'r') as f:
        cities = json.load(f)
else:
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


# Save cities to predefined file
def save():
    """Save current cities to file."""
    os.makedirs(os.path.dirname(CITIES_FILE) or '.', exist_ok=True)
    with open(CITIES_FILE, 'w') as f:
        json.dump(cities, f, indent=2)


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
    
    # Check if higher level state and nations exists
    # If not recursively create them
    city_name = fields[NAME]
    state_name = fields.get(STATE)
    nation_name = fields.get(NATION)
    
    # Check for state and create if non existent
    # Maybe we should standardize all lowercase -ryan
    state_id = None
    for _id, state in states.read().items():
        if state.get(NAME, '').lower() == (state_name or '').lower():
            state_id = _id
            break
    if not state_id and state_name:
        state_id = states.create({NAME: state_name, NATION: nation_name})
    
    # Check for nation using state
    # nation creation is handled by state
    nation_id = None
    state_obj = states.read().get(state_id)
    nation_id = state_obj.get(NATION)
    # Pre-pending underscore because id is a built-in Python function
    _id = str(len(cities) + 1)

    cities[_id] = {
        NAME: city_name,
        STATE: state_id,
        NATION: nation_id
    }
    save()
    return _id


def read() -> dict:
    """Return all cities stored."""
    return cities
