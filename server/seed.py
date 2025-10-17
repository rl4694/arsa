"""
Run `python3 seed.py` to seed our database with starting data from various
APIs. Be sure to empty the database before running this file.
"""

import requests
import time
from server import cities as ct
from server import nations as nt


RAPID_API_HOST = 'wft-geo-db.p.rapidapi.com'
RAPID_API_KEY = 'ba62340b10msh533fb3cfda50da1p1eff9djsn8ca40e19327b'
CITIES_URL = 'https://wft-geo-db.p.rapidapi.com/v1/geo/cities'
NATIONS_URL = 'https://wft-geo-db.p.rapidapi.com/v1/geo/countries'
RESULTS_PER_PAGE = 10
COOLDOWN_SEC = 2


def fetch_rapid_api(url, params):
    """
    Return JSON data from GeoDB API
    """
    headers = {
        'x-rapidapi-host': RAPID_API_HOST,
        'x-rapidapi-key': RAPID_API_KEY,
    }
    res = requests.get(url, headers=headers, params=params)
    if res.status_code != 200:
        raise ConnectionError(
            f'Could not retrieve GeoDB cities: {res.status_code=}'
        )
    return res.json()


def seed_cities(num_cities):
    """
    Add initial city data to our database
    """
    if num_cities < 0:
        raise ValueError(
            f'Requested number of cities cannot be negative {num_cities=}'
        )

    offset = 0
    for i in range(num_cities // RESULTS_PER_PAGE):
        # Fetch city data
        res = fetch_rapid_api(CITIES_URL, {
            'sort': '-population',
            'limit': RESULTS_PER_PAGE,
            'offset': offset,
        })
        if 'data' not in res:
            raise ValueError(f'No data found in GeoDB cities response: {res=}')

        # Add city data to database
        for city in res['data']:
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
    Add all nation data to our database
    """
    offset = 0
    num_nations = None
    while num_nations is None or offset <= num_nations:
        # Fetch city data
        res = fetch_rapid_api(NATIONS_URL, {
            'limit': RESULTS_PER_PAGE,
            'offset': offset,
        })
        if 'data' not in res or 'metadata' not in res:
            raise ValueError(f'No data found in GeoDB nation response: {res=}')

        # Stop if we fetched all countries
        if len(res['data']) == 0:
            break

        # Add city data to database
        for country in res['data']:
            nt.create({
                nt.NAME: country.get('name', ''),
            })

        # Print status
        num_nations = res['metadata']['totalCount']
        print(f"Seeding countries: {nt.length() * 100 // num_nations}%")

        # Wait for rate-limit to wear off
        time.sleep(COOLDOWN_SEC)
        offset += RESULTS_PER_PAGE


if __name__ == '__main__':
    seed_cities(100)
    seed_nations()
