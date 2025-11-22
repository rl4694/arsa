"""
This script seeds seeds our data with data from various APIs.

You can run this script with: `python3 server/seed.py`
Be sure to empty your database before running this file.
"""

import os
import requests
import time
import csv
import zipfile
from dotenv import load_dotenv
from server.controllers import cities as ct
from server.controllers import states as st
from server.controllers import nations as nt
from server.controllers import natural_disasters as nd
from server.common import is_json_populated, save_json
from server.geocoding import reverse_geocode


# Load environment variables
load_dotenv()


# Initialize constants
EARTHQUAKES_DATASET = 'warcoder/earthquake-dataset'
EARTHQUAKES_FILE = 'earthquake_data.csv'

LANDSLIDE_DATASET = 'kazushiadachi/global-landslide-data'
LANDSLIDE_ZIP = 'global-landslide-data.zip'
LANDSLIDE_FILE = 'Global_Landslide_Catalog_Export.csv'

# Potential ones to work on
TSUNAMI_DATASET = 'andrewmvd/tsunami-dataset'
TSUNAMI_FILE = 'tsunami_dataset.csv'

WILDFIRES_DATASET = 'rtatman/188-million-us-wildfires'
WILDFIRES_FILE = 'FPA_FOD_20170508.sqlite'

VOLCANO_DATASET = 'smithsonian/volcanic-eruptions'
VOLCANO_FILE = 'eruptions.csv'

NATIONS_URL = 'https://wft-geo-db.p.rapidapi.com/v1/geo/countries'
RESULTS_PER_PAGE = 10
COOLDOWN_SEC = 1.5

# JSON file paths
NATIONS_JSON_FILE = 'server/json/nations.json'
CITIES_JSON_FILE = 'server/json/cities.json'
STATES_JSON_FILE = 'server/json/states.json'


def get_kaggle_api():
    """
    Return an authenticated Kaggle API which can retrieve datasets
    """
    # Kaggle automatically authenticates during import, so it breaks tests
    # if left in the module scope
    from kaggle.api.kaggle_api_extended import KaggleApi  # noqa: E402
    api = KaggleApi()
    api.authenticate()
    return api


def seed_nations() -> list:
    """
    Add initial nation data from GeoDB nations API to our database

    Returns:
        List of nation IDs created
    """
    offset = 0
    num_nations = None
    result = []
    while num_nations is None or offset <= num_nations:
        # Fetch nation data
        params = {
            'limit': RESULTS_PER_PAGE,
            'offset': offset,
        }
        headers = {
            'x-rapidapi-host': 'wft-geo-db.p.rapidapi.com',
            'x-rapidapi-key': os.getenv('RAPID_API_KEY'),
        }
        try:
            res = requests.get(NATIONS_URL, headers=headers, params=params)
        except requests.exceptions.RequestException as e:
            raise ConnectionError("Could not reach GeoDB nations API") from e

        # Verify response is OK
        if res.status_code != 200:
            raise ConnectionError(
                f'Could not retrieve GeoDB nations: {res.status_code=}'
            )

        # Retrieve data from response
        output = res.json()
        if 'data' not in output or 'metadata' not in output:
            raise ValueError(f'No nations found in GeoDB response: {output=}')

        # Add city data to database
        for country in output['data']:
            name = country.get('name')
            if not name:
                print(f"Skipping country with missing name: {country}")
                continue
            _id = nt.create({nt.NAME: name})
            result.append(_id)

        # Print status
        num_nations = output['metadata']['totalCount']
        completion_percent = nt.length() * 100 // max(num_nations, 1)
        print(f"Seeding countries: {completion_percent}%")

        # Wait for rate-limit to wear off
        time.sleep(COOLDOWN_SEC)
        offset += RESULTS_PER_PAGE

    # Save nations data to JSON file
    try:
        nations_data = nt.read()
        save_json(NATIONS_JSON_FILE, nations_data)
        print(f"Saved {len(nations_data)} nations to {NATIONS_JSON_FILE}")
    except Exception as e:
        print(f"Warning: Could not save nations to JSON: {e}")

    return result


def create_loc_from_coordinates(lat: float, lon: float):
    """
    Use reverse geocoding to resolve coordinates into nation, state, city

    Args:
        lat (float): Latitude
        lon (float): Longitude
    """
    loc = reverse_geocode(lat, lon)
    city_name = loc.get('city')
    state_name = loc.get('state')
    nation_name = loc.get('country')
    if not city_name:
        raise ValueError(f"No city found for ({lat}, {lon})")
    nation_id = (nt.create({nt.NAME: nation_name}) if nation_name else None)
    state_id = None
    if state_name:
        state_id = st.create({
            st.NAME: state_name,
            st.NATION: nation_name
        })
    print(f"Created state: {state_name}, {nation_name}")
    city_id = ct.create({
        ct.NAME: city_name,
        ct.STATE: state_name,
        ct.NATION: nation_name,
    })
    print(f"Created city: {city_name} ({state_name}, {nation_name})")
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
        kaggle_api = get_kaggle_api()
        kaggle_api.dataset_download_file(EARTHQUAKES_DATASET, EARTHQUAKES_FILE)
        with open(EARTHQUAKES_FILE, mode='r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
            for row in rows:
                # Use coordinate data to create nation, state, cities
                lat = float(row['latitude'])
                lon = float(row['longitude'])

                # We'll probably turn this into a separate function soon -RJ
                try:
                    loc_data = create_loc_from_coordinates(lat, lon)
                    city_name = loc_data['city_name']

                    # Create Natural Disaster (Earthquake)
                    disaster_id = nd.create({
                        nd.NAME: f"Earthquake at {city_name}",
                        nd.DISASTER_TYPE: 'earthquake',
                        nd.DATE: row.get('time', ''),
                        nd.LOCATION: f"{lat}, {lon}",
                        nd.DESCRIPTION: f"Magnitude: {row.get('mag', 'N/A')},"
                                        f"Depth: {row.get('depth', 'N/A')} km"
                    })
                    print(f"Created earthquake disaster: {disaster_id}")

                except Exception as e:
                    print(f"Error creating disaster for ({lat}, {lon}): {e}")

    except FileNotFoundError:
        raise ConnectionError('Could not retrieve earthquake CSV file.')
    os.remove(EARTHQUAKES_FILE)


def seed_landslides():
    """
    Add initial landslide data from Kaggle to our database
    """
    try:
        kaggle_api = get_kaggle_api()
        # Unzip CSV file
        kaggle_api.dataset_download_files(LANDSLIDE_DATASET)
        with zipfile.ZipFile(LANDSLIDE_ZIP, 'r') as z:
            z.extractall('.')

        # ignored_words = (
        #     r'\b(road|roads|highway|route|trail|in|near|of|on|and|street|rd)\b'
        # )
        with open(LANDSLIDE_FILE, mode='r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
            for row in rows:
                # Use coordinate data to create nation, state, cities
                lat = float(row['latitude'])
                lon = float(row['longitude'])

                # We'll probably turn this into a separate function soon -RJ
                try:
                    loc_data = create_loc_from_coordinates(lat, lon)
                    city_name = loc_data['city_name']

                    # Create Natural Disaster (Landslide)
                    size = row.get('landslide_size', 'N/A')
                    trigger = row.get('trigger', 'N/A')
                    disaster_id = nd.create({
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
    os.remove(LANDSLIDE_ZIP)
    os.remove(LANDSLIDE_FILE)


# We should try and standardize a format for new disasters
def seed_tsunamis():
    """
    Add initial tsunami data from Kaggle to our database
    """
    try:
        kaggle_api = get_kaggle_api()
        kaggle_api.dataset_download_file(TSUNAMI_DATASET, TSUNAMI_FILE)
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
                    loc_data = create_loc_from_coordinates(lat, lon)
                    city_name = loc_data['city_name']

                    # Create Natural Disaster (Tsunami)
                    disaster_id = nd.create({
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
    os.remove(TSUNAMI_FILE)


if __name__ == '__main__':
    if not is_json_populated(NATIONS_JSON_FILE):
        seed_nations()
    if not is_json_populated(CITIES_JSON_FILE):
        seed_earthquakes()
        seed_landslides()
