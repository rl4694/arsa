"""
This file contains common utilities shared between server modules.
"""

from bson.objectid import ObjectId


def is_valid_id(_id: str) -> bool:
    """Return whether _id is a valid document id"""
    return isinstance(_id, str) and ObjectId.is_valid(_id)
