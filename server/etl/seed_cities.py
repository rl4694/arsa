"""
ETL script for seeding city data
"""

import sys
import server.etl.common as common
import server.controllers.cities as ct


def transform(raw: dict) -> list:
    """Transform city data into format CRUD API can understand"""
    transformed = []
    seen = []
    for city in raw.values():
        # Add city if it is not a duplicate
        new_record = {
            ct.NAME: city['name'],
            ct.STATE_NAME: city['state_name'],
            ct.NATION_NAME: city['nation_name'],
            ct.LATITUDE: city['latitude'],
            ct.LONGITUDE: city['longitude'],
        }
        if not ct.cities.find_duplicate(new_record, search_list=seen):
            seen.append(new_record)
            transformed.append(new_record)
    return transformed


def seed_cities(filename: str):
    """Main seed function to be exported"""
    raw = common.extract_json(filename)
    transformed = transform(raw)
    common.load(ct.cities, transformed)


if __name__ == '__main__':
    seed_cities(common.COORDS_FILE)
