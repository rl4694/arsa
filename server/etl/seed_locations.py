"""
Seed nations, states, and cities by extracting coordinates from disaster CSV
files and reverse geocoding them.

Run with: python3 server/etl/seed_locations.py
"""

import csv
import server.controllers.cities as ct
import server.controllers.states as st
import server.controllers.nations as nt
from server.etl.geocoding import reverse_geocode


ETL_PATH = 'server/etl/'

# Each entry: (csv_filepath, lat_column, lon_column)
DISASTER_FILES = [
    (ETL_PATH + 'earthquakes.csv', 'latitude', 'longitude'),
    (ETL_PATH + 'landslides.csv', 'latitude', 'longitude'),
    (ETL_PATH + 'tsunamis.csv', 'LATITUDE', 'LONGITUDE'),
]


def load_location(lat: float, lon: float) -> dict:
    """
    Reverse geocode coordinates and create nation, state, and city in the DB.

    Args:
        lat (float): Latitude (-90 to 90)
        lon (float): Longitude (-180 to 180)

    Returns:
        dict: Location names with keys city_name, state_name, nation_name

    Raises:
        ValueError: If coordinates are invalid or no city can be resolved
        ConnectionError: If the geocoding service is unavailable
    """
    if not (-90 <= lat <= 90):
        raise ValueError(f"latitude not between -90 and 90: {lat}.")
    if not (-180 <= lon <= 180):
        raise ValueError(f"longitude not between -180 and 180: {lon}.")

    try:
        loc = reverse_geocode(lat, lon)
    except Exception as e:
        raise ConnectionError(f"Geocoding failed for ({lat}, {lon}): {e}")

    city_name = loc.get('city')
    state_name = loc.get('state')
    nation_name = loc.get('country')
    nation_code = loc.get('country_code')

    if not city_name:
        raise ValueError(f"No city found for coordinates ({lat}, {lon})")

    if nation_name:
        try:
            nt.nations.create({
                nt.CODE: nation_code,
                nt.NAME: nation_name,
            })
        except Exception as e:
            print(f"Warning: Failed to create nation '{nation_name}': {e}")

    if state_name and nation_name:
        try:
            st.states.create({
                st.NAME: state_name,
                st.NATION_NAME: nation_name,
            })
            print(f"Created state: {state_name}, {nation_name}")
        except Exception as e:
            print(f"Warning: Failed to create state '{state_name}': {e}")

    if city_name and state_name:
        try:
            ct.cities.create({
                ct.NAME: city_name,
                ct.STATE_NAME: state_name,
                ct.NATION_NAME: nation_name,
                ct.LATITUDE: lat,
                ct.LONGITUDE: lon,
            })
            print(f"Created city: {city_name} ({state_name}, {nation_name})")
        except Exception as e:
            print(f"Warning: Failed to create city '{city_name}': {e}")

    return {
        'city_name': city_name,
        'state_name': state_name,
        'nation_name': nation_name,
    }


def seed_locations(disaster_files=None):
    """
    Iterate over disaster CSV coordinates and create nations, states, and
    cities in the DB via reverse geocoding.

    Args:
        disaster_files: List of (filepath, lat_col, lon_col) tuples.
                        Defaults to DISASTER_FILES.
    """
    if disaster_files is None:
        disaster_files = DISASTER_FILES

    for filepath, lat_col, lon_col in disaster_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    try:
                        lat = float(row[lat_col])
                        lon = float(row[lon_col])
                        load_location(lat, lon)
                    except Exception as e:
                        print(f"Warning: {e}")
        except FileNotFoundError:
            print(f"Warning: File not found: {filepath}")


if __name__ == '__main__':
    seed_locations()
