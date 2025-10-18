"""
Run `python3 seed.py` to seed our database with starting data from various
APIs. Be sure to empty the database before running this file.
"""

import requests
import time
from server import cities as ct
from server import nations as nt

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


if __name__ == '__main__':
    seed_cities(100)
    seed_nations()
