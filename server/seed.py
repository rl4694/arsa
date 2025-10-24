"""
Run `python3 server/seed.py` to seed our database with starting data from
various APIs. Be sure to empty the database before running this file.
"""
import os
import requests
import time
import csv
from server import cities as ct
from server import nations as nt


# Initialize variables relevant to Kaggle
os.environ['KAGGLE_USERNAME'] = "ramon10"
os.environ['KAGGLE_KEY'] = "1f33e052779b4a71bfeab05cab4dc29a"
# Kaggle must be imported after setting environment variables
from kaggle.api.kaggle_api_extended import KaggleApi  # noqa: E402
kaggle_api = KaggleApi()
kaggle_api.authenticate()
EARTHQUAKES_DATASET = 'warcoder/earthquake-dataset'
EARTHQUAKES_FILE = 'earthquake_data.csv'

# Initialize variables relevant to Rapid API
RAPID_API_HEADERS = {
    'x-rapidapi-host': 'wft-geo-db.p.rapidapi.com',
    'x-rapidapi-key': 'ba62340b10msh533fb3cfda50da1p1eff9djsn8ca40e19327b',
}
CITIES_URL = 'https://wft-geo-db.p.rapidapi.com/v1/geo/cities'
NATIONS_URL = 'https://wft-geo-db.p.rapidapi.com/v1/geo/countries'
RESULTS_PER_PAGE = 10
COOLDOWN_SEC = 1


def seed_cities(num_cities: int):
    """
    Add initial city data from GeoDB cities API to our database
    """
    # Validate inputs
    if not isinstance(num_cities, int):
        raise ValueError(f'num_cities must be an integer: {type(num_cities)=}')
    if num_cities < 0:
        raise ValueError(f'num_cities cannot be negative: {num_cities=}')

    offset = 0
    for i in range(num_cities // RESULTS_PER_PAGE):
        # Fetch city data
        params = {
            'sort': '-population',
            'limit': RESULTS_PER_PAGE,
            'offset': offset,
        }
        res = requests.get(CITIES_URL, headers=RAPID_API_HEADERS,
                           params=params)
        if res.status_code != 200:
            raise ConnectionError(
                f'Could not retrieve GeoDB cities: {res.status_code=}'
            )
        output = res.json()
        if 'data' not in output:
            raise ValueError(f'No cities found in GeoDB response: {output=}')

        # Add city data to database
        for city in output['data']:
            ct.create({
                ct.NAME: city.get('name', ''),
                ct.STATE: city.get('region', ''),
                ct.NATION: city.get('country', ''),
            })

        # Print status
        print(f"Seeding cities: {ct.length() * 100 // num_cities}%")

        # Wait for rate-limit to wear off
        time.sleep(COOLDOWN_SEC)
        offset += RESULTS_PER_PAGE


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
    kaggle_api.dataset_download_file(EARTHQUAKES_DATASET, EARTHQUAKES_FILE)
    try:
        with open(EARTHQUAKES_FILE, mode='r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
            # TODO: adjust the number of rows processed
            for row in rows[0:100]:
                print(row)
                # TODO: get actual nations from MongoDB
                nations = []

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

                # TODO: replace print with natural disaster creation
                print({
                    'city': city,
                    'state': state,
                    'nation': nation,
                })
    except FileNotFoundError:
        raise ConnectionError('Could not retrieve earthquake CSV file.')
    os.remove(EARTHQUAKES_FILE)


if __name__ == '__main__':
    # seed_cities(100)
    # seed_nations()
    seed_earthquakes()
