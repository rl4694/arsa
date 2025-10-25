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
from server import nations as nt


# Initialize variables relevant to Kaggle
os.environ['KAGGLE_USERNAME'] = "ramon10"
os.environ['KAGGLE_KEY'] = "1f33e052779b4a71bfeab05cab4dc29a"
EARTHQUAKES_DATASET = 'warcoder/earthquake-dataset'
EARTHQUAKES_FILE = 'earthquake_data.csv'
LANDSLIDE_DATASET = 'kazushiadachi/global-landslide-data'
LANDSLIDE_ZIP = 'global-landslide-data.zip'
LANDSLIDE_FILE = 'Global_Landslide_Catalog_Export.csv'

# Initialize variables relevant to Rapid API
RAPID_API_HEADERS = {
    'x-rapidapi-host': 'wft-geo-db.p.rapidapi.com',
    'x-rapidapi-key': 'ba62340b10msh533fb3cfda50da1p1eff9djsn8ca40e19327b',
}
CITIES_URL = 'https://wft-geo-db.p.rapidapi.com/v1/geo/cities'
NATIONS_URL = 'https://wft-geo-db.p.rapidapi.com/v1/geo/countries'
RESULTS_PER_PAGE = 10
COOLDOWN_SEC = 1


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
        res = requests.get(NATIONS_URL, headers=RAPID_API_HEADERS,
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
            nations = nt.read()
            for row in rows:
                # If location is not in the expected format, skip it
                location = row['location'].split(', ')
                if len(location) != 2:
                    continue

                # Extract location data from row
                city = location[0]
                state = ''
                nation = ''
                if location[1] in nations:
                    nation = location[1]
                else:
                    state = location[1]
                if row['country'] in nations:
                    nation = row['country']

                # Create location in database
                ct.create({
                    ct.NAME: city,
                    ct.STATE: state,
                    ct.NATION: nation,
                })
                # TODO: create natural disasters
                print(row['latitude'], row['longitude'])

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
    # seed_nations()
    seed_earthquakes()
    seed_landslides()
