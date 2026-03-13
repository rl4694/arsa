"""
Seed nations, states, and cities by extracting coordinates from disaster CSV
files and reverse geocoding them.

Run with: python3 server/etl/seed_locations.py
"""

import csv
import server.controllers.cities as ct
import server.controllers.states as st
import server.controllers.nations as nt
from server.controllers.geocoding import reverse_geocode


ETL_PATH = 'server/etl/'

# Each entry: (csv_filepath, lat_column, lon_column)
DISASTER_FILES = [
    (ETL_PATH + 'earthquakes.csv', 'latitude', 'longitude'),
    (ETL_PATH + 'landslides.csv', 'latitude', 'longitude'),
    (ETL_PATH + 'tsunamis.csv', 'LATITUDE', 'LONGITUDE'),
]


def extract(filename: str) -> list:
    """Extract location data from its CSV file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            extracted = csv.DictReader(f)
            return list(extracted)
    except FileNotFoundError:
        print(f"Warning: File not found: {filename}")


def transform(raw: list, lat_col: str, lon_col: str) -> tuple:
    """
    Transform disaster file coordinates into city and state data

    Raises:
        ValueError: If coordinates are invalid or no city can be resolved
    """
    transformed_cities = []
    transformed_states = []
    for row in raw:
        try:
            # Extract the coordinates
            lat = float(row[lat_col])
            lon = float(row[lon_col])

            # Validate the coordinates
            if not (-90 <= lat <= 90):
                raise ValueError(f"latitude not between -90 and 90: {lat}.")
            if not (-180 <= lon <= 180):
                raise ValueError(f"longitude not between -180 and 180: {lon}.")
            
            # Convert coordinates into location
            loc = reverse_geocode(lat, lon)
            city_name = loc.get('city')
            state_name = loc.get('state')
            nation_name = loc.get('country')

            # Validate location is not empty
            if not (city_name and state_name and nation_name):
                raise ValueError(f"No location found for coordinates ({lat}, {lon})")
            
            transformed_cities.append({
                ct.NAME: city_name,
                ct.STATE_NAME: state_name,
                ct.NATION_NAME: nation_name,
                ct.LATITUDE: lat,
                ct.LONGITUDE: lon,
            })
            transformed_states.append({
                st.NAME: city_name,
                ct.NATION_NAME: nation_name,
            })
        except Exception as e:
            print(f"Warning: {e}")
    return transformed_cities, transformed_states


def load_cities(transformed: list):
    try:
        ct.cities.create_many(transformed)
        print(f"Created cities")
    except Exception as e:
        print(f"Warning: Failed to create cities: {e}")


def load_states(transformed: list):
    try:
        st.states.create_many(transformed)
        print(f"Created states")
    except Exception as e:
        print(f"Warning: Failed to create states: {e}")


def seed_locations(disaster_files):
    """
    Iterate over disaster CSV coordinates and create nations, states, and
    cities in the DB via reverse geocoding.

    Args:
        disaster_files: List of (filepath, lat_col, lon_col) tuples.
                        Defaults to DISASTER_FILES.
    """
    for filepath, lat_col, lon_col in disaster_files:
        raw = extract(filepath)
        transformed_cities, transformed_states = transform(raw, lat_col, lon_col)
        load_cities(transformed_cities)
        load_states(transformed_states)


if __name__ == '__main__':
    seed_locations(DISASTER_FILES)
