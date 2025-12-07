"""
This script seeds seeds our data with data from various APIs.

You can run this script with: `python3 server/etl/seed.py`
Be sure to empty your database before running this file.
"""

import os
import requests
import time
import csv
import zipfile
import server.controllers.cities as ct
import server.controllers.states as st
import server.controllers.nations as nt
import server.controllers.natural_disasters as nd
from server.common import is_json_populated, save_json
from server.geocoding import reverse_geocode
from server.etl.seed_nations import seed_nations
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


# Initialize constants
ETL_PATH = 'server/etl/'
EARTHQUAKES_FILE = ETL_PATH + 'earthquakes.csv'
LANDSLIDE_FILE = ETL_PATH + 'landslides.csv'
TSUNAMI_FILE = ETL_PATH + 'tsunamis.csv'
CITIES_JSON_FILE = ETL_PATH + 'cities.json'
STATES_JSON_FILE = ETL_PATH + 'states.json'
DISASTERS_JSON_FILE = ETL_PATH + 'disasters.json'

# Potential ones to work on
WILDFIRES_DATASET = 'rtatman/188-million-us-wildfires'
WILDFIRES_FILE = 'FPA_FOD_20170508.sqlite'

VOLCANO_DATASET = 'smithsonian/volcanic-eruptions'
VOLCANO_FILE = 'eruptions.csv'


def get_kaggle_api():
    """
    Return an authenticated Kaggle API which can retrieve datasets.

    Returns:
        KaggleApi: Authenticated Kaggle API client

    Raises:
        OSError: If Kaggle credentials are not configured

    Note:
        Requires ~/.kaggle/kaggle.json with API credentials.
        Get credentials from: https://www.kaggle.com/settings/account
    """
    # Kaggle automatically authenticates during import, so it breaks tests
    # if left in the module scope
    from kaggle.api.kaggle_api_extended import KaggleApi  # noqa: E402

    try:
        api = KaggleApi()
        api.authenticate()
        return api
    except OSError as e:
        raise OSError(
            "Kaggle API authentication failed. "
            "Ensure ~/.kaggle/kaggle.json exists with valid credentials."
            f"Error: {e}"
        ) from e


def seed_location(lat: float, lon: float):
    """
    Use reverse geocoding to resolve coordinates into nation, state, city.

    Args:
        lat (float): Latitude (-90 to 90)
        lon (float): Longitude (-180 to 180)

    Returns:
        dict: Dictionary containing created IDs and location names

    Raises:
        ValueError: If coordinates are invalid or city cannot be found
        ConnectionError: If geocoding service is unavailable
    """
    # Validate coordinates
    if not (-90 <= lat <= 90):
        raise ValueError(f"latitude not between -90 and 90: {lat}.")
    if not (-180 <= lon <= 180):
        raise ValueError(f"longitude not between -180 and 180: {lon}.")

    # Attempt reverse geocoding with error handling
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

    # Create nation (if provided)
    nation_id = None
    if nation_name:
        try:
            nation_id = nt.nations.create({
                nt.CODE: nation_code,
                nt.NAME: nation_name
            })
        except Exception as e:
            print(f"Warning: Failed to create nation '{nation_name}': {e}")

    # Create state (if provided)
    state_id = None
    if state_name and nation_name:
        try:
            state_id = st.states.create({
                st.NAME: state_name,
                st.NATION_NAME: nation_name
            })
            print(f"Created state: {state_name}, {nation_name}")
        except Exception as e:
            print(f"Warning: Failed to create state '{state_name}': {e}")

    # Create city
    try:
        city_id = ct.cities.create({
            ct.NAME: city_name,
            ct.STATE_NAME: state_name,
            ct.NATION_NAME: nation_name,
        })
        print(f"Created city: {city_name} ({state_name}, {nation_name})")
    except Exception as e:
        raise RuntimeError(f"Warning: Failed to create city '{city_name}': {e}") from e

    return {
        'city': city_id,
        'state': state_id,
        'nation': nation_id,
        'city_name': city_name,
        'state_name': state_name,
        'nation_name': nation_name,
    }


def seed_earthquakes():
    """
    Add initial earthquake data from Kaggle to our database
    """
    try:
        rows = []
        with open(EARTHQUAKES_FILE, mode='r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))

        for i, row in enumerate(rows):
            print(f'{i} out of {len(rows)} seeded.')
            # Use coordinate data to create nation, state, cities
            lat = float(row['latitude'])
            lon = float(row['longitude'])

            # We'll probably turn this into a separate function soon -RJ
            try:
                loc_data = seed_location(lat, lon)
                city_name = loc_data['city_name']

                # Create Natural Disaster (Earthquake)
                disaster_id = nd.disasters.create({
                    nd.NAME: f"Earthquake at {city_name}",
                    nd.DISASTER_TYPE: 'earthquake',
                    nd.DATE: row.get('time', ''),
                    nd.LOCATION: f"{lat}, {lon}",
                    nd.DESCRIPTION: f"Magnitude: {row.get('mag', 'N/A')},"
                                    f"Depth: {row.get('depth', 'N/A')} km"
                })
                print(f"Created earthquake disaster: {disaster_id}")

            except Exception as e:
                print(e)

    except FileNotFoundError:
        raise ConnectionError('Could not retrieve earthquake CSV file.')


def seed_landslides():
    """
    Add initial landslide data from Kaggle to our database
    """
    try:
        rows = []
        with open(LANDSLIDE_FILE, mode='r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            # Use coordinate data to create nation, state, cities
            lat = float(row['latitude'])
            lon = float(row['longitude'])

            # We'll probably turn this into a separate function soon -RJ
            try:
                loc_data = seed_location(lat, lon)
                city_name = loc_data['city_name']

                # Create Natural Disaster (Landslide)
                size = row.get('landslide_size', 'N/A')
                trigger = row.get('trigger', 'N/A')
                disaster_id = nd.disasters.create({
                    nd.NAME: f"Landslide at {city_name}",
                    nd.DISASTER_TYPE: 'landslide',
                    nd.DATE: row.get('event_date', ''),
                    nd.LOCATION: f"{lat}, {lon}",
                    nd.DESCRIPTION: f"Size: {size}, Trigger: {trigger}"
                })
                print(f"Created landslide: {disaster_id} at {lat}, {lon}")

            except Exception as e:
                print(f"Error creating disaster for ({lat}, {lon}): {e}")
    except FileNotFoundError:
        raise ConnectionError('Could not retrieve tsunami CSV file.')


# We should try and standardize a format for new disasters
def seed_tsunamis():
    """
    Add initial tsunami data from Kaggle to our database
    """
    try:
        rows = []
        with open(TSUNAMI_FILE, mode='r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            # general long and lat parser module
            lat_str = (
                row.get('latitude') or row.get('Latitude') or
                row.get('lat') or row.get('Lat')
            )
            lon_str = (
                row.get('longitude') or row.get('Longitude') or
                row.get('lon') or row.get('Lon') or row.get('lng')
            )

            if not lat_str or not lon_str:
                continue

            lat = float(str(lat_str).strip())
            lon = float(str(lon_str).strip())

            try:
                loc_data = seed_location(lat, lon)
                city_name = loc_data['city_name']

                # Create Natural Disaster (Tsunami)
                disaster_id = nd.disasters.create({
                    nd.NAME: f"Tsunami at {city_name}",
                    nd.DISASTER_TYPE: 'tsunami',
                    nd.DATE: row.get('time', ''),
                    nd.LOCATION: f"{lat}, {lon}"
                    # nd.DESCRIPTION:
                })
                print(f"Created tsunami disaster: {disaster_id}")

            except Exception as e:
                print(f"Error creating disaster for ({lat}, {lon}): {e}")

    except FileNotFoundError:
        raise ConnectionError('Could not retrieve tsunami CSV file.')


def main():
    seed_nations()

    if (not is_json_populated(CITIES_JSON_FILE) or
            not is_json_populated(STATES_JSON_FILE)):
        print("Seeding cities and states from disaster data...")
        seed_earthquakes()
        seed_landslides()
        seed_tsunamis()

    # Save cities and states to JSON files
    try:
        cities_data = ct.cities.read()
        save_json(CITIES_JSON_FILE, cities_data)
        print(f"Saved {len(cities_data)} cities to {CITIES_JSON_FILE}")
    except Exception as e:
        print(f"Warning: Could not save cities to JSON: {e}")

    try:
        states_data = st.states.read()
        save_json(STATES_JSON_FILE, states_data)
        print(f"Saved {len(states_data)} states to {STATES_JSON_FILE}")
    except Exception as e:
        print(f"Warning: Could not save states to JSON: {e}")

    try:
        disasters_data = nd.disasters.read()
        save_json(DISASTERS_JSON_FILE, disasters_data)
        print(f"Saved {len(disasters_data)} states to {DISASTERS_JSON_FILE}")
    except Exception as e:
        print(f"Warning: Could not save states to JSON: {e}")

    print("Seeding complete")


if __name__ == '__main__':
    main()
