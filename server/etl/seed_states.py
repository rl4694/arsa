"""
ETL script for seeding state data
"""

import sys
import server.etl.common as common
import server.controllers.states as st


def transform(raw: dict) -> list:
    """Transform state data into format CRUD API can understand"""
    transformed = []
    seen = []
    for state in raw.values():
        # Add state if it is not a duplicate
        new_record = {
            st.NAME: state['name'],
            st.NATION_NAME: state['nation_name'],
        }
        if not st.states.find_duplicate(new_record, search_list=seen):
            seen.append(new_record)
            transformed.append(new_record)
    return transformed


def seed_states(filename: str):
    """Main seed function to be exported"""
    raw = common.extract_json(filename)
    transformed = transform(raw)
    common.load(st.states, transformed)


if __name__ == '__main__':
    seed_states(common.COORDS_FILE)
