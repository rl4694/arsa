# server/states.py
import os
import json
from server import nations

MIN_ID_LEN = 1
NAME = 'name'
NATION = 'nation'

STATES_FILE = 'states.json'

# Load states from predefined file if exists, else load the local
if os.path.exists(STATES_FILE):
    with open(STATES_FILE, 'r') as f:
        states = json.load(f)
else:
    states = {}


def is_valid_id(_id: str) -> bool:
    """Return True if _id is a non-empty string."""
    if not isinstance(_id, str):
        return False
    if len(_id) < MIN_ID_LEN:
        return False
    return True


def length() -> int:
    """Return the number of states stored."""
    return len(states)
    
    
# Save states to predefined file
def save():
    """Save current states to file."""
    os.makedirs(os.path.dirname(STATES_FILE) or '.', exist_ok=True)
    with open(STATES_FILE, 'w') as f:
        json.dump(states, f, indent=2)


def create(fields: dict) -> str:
    """
    Create a new state record.
    Requires a dict with a 'name' key.
    Optional Nation field
    Returns a string id.
    """
    if not isinstance(fields, dict):
        raise ValueError(f'Bad type for fields: {type(fields)}')
    if not fields.get(NAME):
        raise ValueError(f'Name missing in fields: {fields.get(NAME)}')

    
    # Check if higher level nation exists, if not create
    state_name = fields[NAME]
    nation_name = fields.get(NATION)
    
    nation_id = None
    for _id, nation in nations.read().items():
        if nation.get(NAME, '').lower() == (nation_name or '').lower():
            nation_id = _id
            break
    if not nation_id and nation_name:
        nation_id = nations.create({NAME: nation_name})
    
    _id = str(len(states) + 1)
    states[_id] = {
        NAME: state_name,
        NATION: nation_id
    }
    save()
    return _id
    
def read() -> dict:
    return states
