import json
import os


def save_json(filename: str, data: dict):
    """Save data to JSON file."""
    if not isinstance(data, dict):
        raise ValueError(f'Bad type for data: {type(data)}')

    os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


def load_json(filename: str) -> dict:
    """Load data from JSON file."""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"JSON file not found: {filename=}")

    with open(filename, 'r') as f:
        return json.load(f)
