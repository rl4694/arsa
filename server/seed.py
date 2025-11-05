"""
Run `python3 server/seed.py` to seed our database with starting data from
various APIs. Be sure to empty the database before running this file.
"""
import os
import requests
import time
import csv
import zipfile
import re
from dotenv import load_dotenv
from server.controllers import cities as ct
from server.controllers import states as st
from server.controllers import nations as nt
from server.controllers.utils import is_json_populated, save_json, load_json
from server.geocoding import reverse_geocode


# Load environment variables
load_dotenv()


# Initialize constants
EARTHQUAKES_DATASET = 'warcoder/earthquake-dataset'
EARTHQUAKES_FILE = 'earthquake_data.csv'

LANDSLIDE_DATASET = 'kazushiadachi/global-landslide-data'
LANDSLIDE_ZIP = 'global-landslide-data.zip'
LANDSLIDE_FILE = 'Global_Landslide_Catalog_Export.csv'

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


def seed_nations(skip_if_populated=True) -> list:
    """
    Add initial nation data from GeoDB nations API to our database
    
    Args:
        skip_if_populated: If True, skip seeding if JSON file already has data
    
    Returns:
        List of nation IDs created
    """
    # Check if JSON file is already populated
    if skip_if_populated and is_json_populated(NATIONS_JSON_FILE):
        print(f"Nations JSON file already populated, skipping seed_nations")
        return []
    
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
        res = requests.get(NATIONS_URL, headers=headers,
                           params=params)

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
            _id = nt.create({
                nt.NAME: country.get('name', ''),
            })
            result.append(_id)

        # Print status
        num_nations = output['metadata']['totalCount']
        print(f"Seeding countries: {nt.length() * 100 // num_nations}%")

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
            st.NATION: nation_id
        })
    print(f"Created state: {state_name}, {nation_name}")
    city_id = ct.create({
        ct.NAME: city_name,
        ct.STATE: state_id,
        ct.NATION: nation_id,
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


def seed_earthquakes(skip_if_populated=True):
    """
    Add initial earthquake data from Kaggle to our database
    
    Args:
        skip_if_populated: If True, skip seeding if JSON file already has data
    """
    # Check if JSON file is already populated
    if skip_if_populated and is_json_populated(CITIES_JSON_FILE):
        print(f"Cities JSON file already populated, skipping seed_earthquakes")
        return
    
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
                    location = create_loc_from_coordinates(lat, lon)

                except Exception:
                    print(f"Error geocoding for ({lat}, {lon})")
                # TODO: create natural disasters
                # print(row['latitude'], row['longitude'])

    except FileNotFoundError:
        raise ConnectionError('Could not retrieve earthquake CSV file.')
    os.remove(EARTHQUAKES_FILE)


def seed_landslides(skip_if_populated=True):
    """
    Add initial landslide data from Kaggle to our database
    
    Args:
        skip_if_populated: If True, skip seeding if JSON file already has data
    """
    # Check if JSON file is already populated
    if skip_if_populated and is_json_populated(CITIES_JSON_FILE):
        print(f"Cities JSON file already populated, skipping seed_landslides")
        return
    
    try:
        kaggle_api = get_kaggle_api()
        # Unzip CSV file
        kaggle_api.dataset_download_files(LANDSLIDE_DATASET)
        with zipfile.ZipFile(LANDSLIDE_ZIP, 'r') as z:
            z.extractall('.')

        ignored_words = (
            r'\b(road|roads|highway|route|trail|in|near|of|on|and|street|rd)\b'
        )
        with open(LANDSLIDE_FILE, mode='r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
            for row in rows:
                # Use coordinate data to create nation, state, cities
                lat = float(row['latitude'])
                lon = float(row['longitude'])

                # We'll probably turn this into a separate function soon -RJ
                try:
                    location = create_loc_from_coordinates(lat, lon)

                except Exception:
                    print(f"Error geocoding for ({lat}, {lon})")
                # TODO: create natural disasters
                # print(row['latitude'], row['longitude'])
    except FileNotFoundError:
        raise ConnectionError('Could not retrieve tsunami CSV file.')
    os.remove(LANDSLIDE_ZIP)
    os.remove(LANDSLIDE_FILE)


if __name__ == '__main__':
    seed_nations()
    seed_earthquakes()
    seed_landslides()
