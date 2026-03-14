"""
ETL script for seeding state data
"""

import sys
import json
import server.controllers.states as st


def extract(filename: str) -> list:
    """Extract state data from its file"""
    try:
        with open(filename) as f:
            extracted = json.load(f)
            return list(extracted.values())
    except Exception as e:
        print(f'Problem reading file: {str(e)}')
        exit(1)


def transform(raw: list) -> list:
    """Transform state data into format CRUD API can understand"""
    transformed = []
    seen = set()
    for state in raw:
        # Build key fields
        keys = []
        for key in st.KEY:
            keys.append(state[key])
        
        # Add state if it is not a duplicate
        if tuple(keys) not in seen:
            seen.add(tuple(keys))
            transformed.append({
                st.NAME: state['name'],
                st.NATION_NAME: state['nation_name'],
            })
    return transformed


def load(transformed: list):
    """Load state data into database"""
    try:
        st.states.create_many(transformed)
    except Exception as e:
        print("Warning: Failed to create states,", e)


def seed_states(filename: str):
    """Main seed function to be exported"""
    raw = extract(filename)
    transformed = transform(raw)
    load(transformed)


if __name__ == '__main__':
    seed_states('server/etl/coords.json')
