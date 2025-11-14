"""
This file contains common utilities shared between server modules.
"""

import os
import json
from bson.objectid import ObjectId


def is_valid_id(_id: str) -> bool:
    """Return whether _id is a valid document id"""
    return isinstance(_id, str) and ObjectId.is_valid(_id)


def save_json(filename: str, data: dict):
    if not isinstance(data, dict):
        raise ValueError(f'Bad type for data: {type(data)}')
    os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


def load_json(filename: str) -> dict:
    if not os.path.exists(filename):
        raise FileNotFoundError(f"JSON file not found: {filename=}")
    with open(filename, 'r') as f:
        return json.load(f)


def is_json_populated(filename: str) -> bool:
    """
    Check if a JSON file exists and contains non-empty data.

    Args:
        filename: Path to the JSON file

    Returns:
        True if file exists and contains data (non-empty dict/list)
        False otherwise
    """
    if not os.path.exists(filename):
        return False

    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            # Check if data is a non-empty dict or list
            if isinstance(data, dict):
                return len(data) > 0
            elif isinstance(data, list):
                return len(data) > 0
            else:
                return False
    except (json.JSONDecodeError, IOError):
        return False
