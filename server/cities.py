import os
import json

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

    # Pre-pending underscore because id is a built-in Python function
    _id = str(len(cities) + 1)
    # Currently state and nation are optional for testing, will implement proper ID in fields later with creation logic
    cities[_id] = {
        NAME: fields[NAME],
        STATE: fields.get(STATE),
        NATION: fields.get(NATION)
    }
    save()
    return _id


def read() -> dict:
    """Return all cities stored."""
    return cities
