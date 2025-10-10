MIN_ID_LEN = 1
NAME = 'name'


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
    Returns a string id.
    """
    if not isinstance(fields, dict):
        raise ValueError(f'Bad type for fields: {type(fields)}')
    if not fields.get(NAME):
        raise ValueError(f'Name missing in fields: {fields.get(NAME)}')

    # Pre-pending underscore because id is a built-in Python function
    _id = str(len(cities) + 1)
    cities[_id] = fields
    return _id


def read() -> dict:
    """Return all cities stored."""
    return cities
