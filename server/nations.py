# server/nations.py

MIN_ID_LEN = 1
NAME = 'name'

nations = {}


def is_valid_id(_id: str) -> bool:
    if not isinstance(_id, str):
        return False
    if len(_id) < MIN_ID_LEN:
        return False
    return True


def length():
    return len(nations)


def create(fields: dict) -> str:
    if not isinstance(fields, dict):
        raise ValueError(f'Bad type for fields: {type(fields)}')
    if not fields.get(NAME):
        raise ValueError(f'Name missing in fields: {fields.get(NAME)}')

    # Pre-pending underscore because id is a built-in Python function
    _id = str(len(nations) + 1)
    nations[_id] = fields
    return _id


def read() -> dict:
    return nations
