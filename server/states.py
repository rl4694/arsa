# server/states.py

MIN_ID_LEN = 1
NAME = 'name'

# In-memory storage for states
states = {}
current_id = 0


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
    Returns a string id.
    """
    if not isinstance(fields, dict):
        raise ValueError(f'Bad type for fields: {type(fields)}')
    if not fields.get(NAME):
        raise ValueError(f'Name missing in fields: {fields.get(NAME)}')

    global current_id
    current_id += 1
    _id = str(current_id)
    states[_id] = fields
    return _id
