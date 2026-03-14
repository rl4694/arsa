"""
ETL script for mapping disaster coordinates to locations
"""

import csv
import json
import os
import sys
import server.controllers.cities as ct
import server.controllers.states as st
import server.controllers.nations as nt
from server.controllers.geocoding import reverse_geocode


COORDS_FILE = 'server/etl/coords.json'


def extract(filename: str) -> list:
    """Extract coordinate data from CSV file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            extracted = csv.DictReader(f)
            return list(extracted)
    except FileNotFoundError:
        print(f"Warning: File not found: {filename}")


def transform(raw: list, lat_col: str, lon_col: str) -> tuple:
    """
    Transform disaster file coordinates into location data

    Raises:
        ValueError: If coordinates are invalid or no city can be resolved
    """
    transformed = {}
    count = 0
    for row in raw:
        try:
            # Update progress
            count += 1
            print(f"Transforming: {count} / {len(raw)}")

            # Extract the coordinates
            lat = float(row[lat_col])
            lon = float(row[lon_col])

            # Convert coordinates into location
            loc = reverse_geocode(lat, lon)
            city_name = loc.get('city')
            state_name = loc.get('state')
            nation_name = loc.get('country')

            # Validate location is not empty
            if not (city_name and state_name and nation_name):
                raise ValueError(f"No location found for coordinates ({lat}, {lon})")
            
            # Use coordinate string as the key
            key = f"{lat:06f},{lon:06f}"
            transformed[key] = {
                ct.NAME: city_name,
                ct.STATE_NAME: state_name,
                ct.NATION_NAME: nation_name,
                ct.LATITUDE: lat,
                ct.LONGITUDE: lon,
            }
        except Exception as e:
            print(f"Warning: {e}")
    return transformed


def load(transformed: dict):
    if not isinstance(transformed, dict):
        raise ValueError(f'Bad type for data: {type(transformed)}')

    # Create JSON file if it doesn't exist
    os.makedirs(os.path.dirname(COORDS_FILE) or '.', exist_ok=True)

    # Read existing data in JSON file
    data = {}
    try:
        with open(COORDS_FILE, 'r') as f:
            data = json.load(f)
    except:
        data = {}

    # Add transformed to data
    data.update(transformed)

    # Write data back into JSON file
    with open(COORDS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def seed_coords(filename: str, lat_col: str, lon_col:str):
    """
    Iterate over disaster CSV coordinates and save location mappings in
    JSON file via reverse geocoding.

    Args:
        filename: name of disaster CSV file
        lat_col: name of latitude column in CSV file
        lon_col: name of longitude column in CSV file
    """
    if not (isinstance(filename, str) and isinstance(lat_col, str) and isinstance(lon_col, str)):
        raise ValueError("Error seeding coordinates: filename, lat_col, and lon_col must be strings")

    raw = extract(filename)
    transformed = transform(raw, lat_col, lon_col)
    load(transformed)


def main():
    if len(sys.argv) < 4:
        print("Usage: python -m server.controllers.seed_coords.py <input_file> <latitude_col> <longitude_col>")
        exit(1)
    # Seed locations using CLI arguments
    seed_coords(sys.argv[1], sys.argv[2], sys.argv[3])


if __name__ == '__main__':
    main()
