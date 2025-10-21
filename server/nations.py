# server/nations.py
import os
import json

MIN_ID_LEN = 1
NAME = 'name'

NATIONS_FILE = 'nations.json'

# Load nations from predefined file if exists, else load the local
if os.path.exists(NATIONS_FILE):
    with open(NATIONS_FILE, 'r') as f:
        nations = json.load(f)
else:
    nations = {}


def is_valid_id(_id: str) -> bool:
    if not isinstance(_id, str):
        return False
    if len(_id) < MIN_ID_LEN:
        return False
    return True


def length():
    return len(nations)


# Save nations to predefined file
def save():
    """Save current nations to file."""
    os.makedirs(os.path.dirname(NATIONS_FILE) or '.', exist_ok=True)
    with open(NATIONS_FILE, 'w') as f:
        json.dump(nations, f, indent=2)


def create(fields: dict) -> str:
    if not isinstance(fields, dict):
        raise ValueError(f'Bad type for fields: {type(fields)}')
    if not fields.get(NAME):
        raise ValueError(f'Name missing in fields: {fields.get(NAME)}')
    
    # Check for duplicates
    new_name = fields[NAME].strip().lower()
    for _id, nation in nations.items():
        if nation.get(NAME, '').strip().lower() == new_name:
            return _id
            
    # Pre-pending underscore because id is a built-in Python function
    _id = str(len(nations) + 1)
    nations[_id] = fields
    save()
    return _id


def read() -> dict:
    return nations
