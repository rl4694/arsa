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
from server import cities as ct
from server import states as st
from server import nations as nt
from dotenv import load_dotenv
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


def seed_nations():
    """
    Add initial nation data from GeoDB nations API to our database
    """
    offset = 0
    num_nations = None
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
        if res.status_code != 200:
            raise ConnectionError(
                f'Could not retrieve GeoDB nations: {res.status_code=}'
            )
        output = res.json()
        if 'data' not in output or 'metadata' not in output:
            raise ValueError(f'No nations found in GeoDB response: {output=}')

        # Add city data to database
        for country in output['data']:
            nt.create({
                nt.NAME: country.get('name', ''),
            })

        # Print status
        num_nations = output['metadata']['totalCount']
        print(f"Seeding countries: {nt.length() * 100 // num_nations}%")

        # Wait for rate-limit to wear off
        time.sleep(COOLDOWN_SEC)
        offset += RESULTS_PER_PAGE


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
                    # Use reverse geocode module to resolve latitude and longitude
                    loc = reverse_geocode(lat, lon)
                    city_name = loc.get('city')
                    state_name = loc.get('state')
                    nation_name = loc.get('country')
                    
                    if not city_name:
                        print(f"No city found for ({lat}, {lon})")
                        continue
                        
                    # Create Nation
                    nation_id = nt.create({nt.NAME: nation_name}) if nation_name else None
                    print(f"Created nation: {loc.get('country')}")
                    
                    # Create State
                    state_id = None
                    if state_name:
                        state_id = st.create({
                            st.NAME: state_name,
                            st.NATION: nation_id
                        })
                    print(f"Created state: {{loc.get('state')}, {loc.get('country')}")
                    
                    # Create City
                    city_id = ct.create({
                        ct.NAME: city_name,
                        ct.STATE: state_id,
                        ct.NATION: nation_id,
                    })
                    print(f"Created city: {loc['city']} ({loc.get('state')}, {loc.get('country')})")

                except Exception as e:
                    print(f"Error geocoding for ({lat}, {lon})")
                # TODO: create natural disasters
                # print(row['latitude'], row['longitude'])

    except FileNotFoundError:
        raise ConnectionError('Could not retrieve earthquake CSV file.')
    os.remove(EARTHQUAKES_FILE)


def seed_landslides():
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
            nations = nt.read()
            for row in rows:
                # If location is not in the expected format or contains
                # ignored words, skip it
                location = row['location_description'].split(', ')
                if (len(location) != 2
                        or re.search(
                            ignored_words,
                            row['location_description'],
                            flags=re.IGNORECASE
                        )
                        or re.search(r'\d', row['location_description'])):
                    continue

                # Extract location data from row
                city = location[0]
                state = ''
                nation = ''
                if location[1] in nations:
                    nation = location[1]
                else:
                    state = location[1]
                if row['country_name'] in nations:
                    nation = row['country_name']

                # Create location in database
                ct.create({
                    ct.NAME: city,
                    ct.STATE: state,
                    ct.NATION: nation,
                })
                # TODO: create natural disasters
                print(row['latitude'], row['longitude'])
    except FileNotFoundError:
        raise ConnectionError('Could not retrieve tsunami CSV file.')
    os.remove(LANDSLIDE_ZIP)
    os.remove(LANDSLIDE_FILE)


if __name__ == '__main__':
    seed_nations()
    seed_earthquakes()
    seed_landslides()
