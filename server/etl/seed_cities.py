"""
ETL script for seeding city data
"""

import sys
import json
import server.controllers.cities as ct


def extract(filename: str) -> list:
    """Extract city data from its file"""
    try:
        with open(filename) as f:
            extracted = json.load(f)
            return list(extracted.values())
    except Exception as e:
        print(f'Problem reading file: {str(e)}')
        exit(1)


def transform(raw: list) -> list:
    """Transform city data into format CRUD API can understand"""
    transformed = []
    seen = set()
    for city in raw:
        # Build key fields
        keys = []
        for key in ct.KEY:
            keys.append(city[key])
        
        # Add city if it is not a duplicate
        if tuple(keys) not in seen:
            seen.add(tuple(keys))
            transformed.append({
                ct.NAME: city['name'],
                ct.STATE_NAME: city['state_name'],
                ct.NATION_NAME: city['nation_name'],
                ct.LATITUDE: city['latitude'],
                ct.LONGITUDE: city['longitude'],
            })
    return transformed


def load(transformed: list):
    """Load city data into database"""
    try:
        ct.cities.create_many(transformed)
    except Exception as e:
        print("Warning: Failed to create cities,", e)


def seed_cities(filename: str):
    """Main seed function to be exported"""
    raw = extract(filename)
    transformed = transform(raw)
    load(transformed)


if __name__ == '__main__':
    seed_cities('server/etl/coords.json')
