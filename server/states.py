# server/states.py

MIN_ID_LEN = 1
NAME = 'name'
NATION = 'nation'

# In-memory storage for states
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

    _id = str(len(states) + 1)
    states[_id] = {
        NAME: fields[NAME],
        NATION: fields.get(NATION)
    }
    return _id

def read() -> dict:
    """Return all states stored."""
    return states
