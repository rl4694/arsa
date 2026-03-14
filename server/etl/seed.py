"""
This script seeds our data with data from various APIs.

You can run this script with: `python3 server/etl/seed.py`
Be sure to empty your database before running this file.
"""

import os
import json
import server.controllers.cities as ct
import server.controllers.states as st
import server.controllers.nations as nt
import server.controllers.natural_disasters as nd
from server.etl.seed_nations import seed_nations
from server.etl.clear_db import clear_db
import server.etl.seed_disasters as sd
import server.etl.seed_coords as scd
import server.etl.seed_cities as sct
import server.etl.seed_states as ss


# Initialize constants
ETL_PATH = 'server/etl/'
NATIONS_FILE = ETL_PATH + 'nations.csv'
EARTHQUAKES_FILE = ETL_PATH + 'earthquakes.csv'
LANDSLIDE_FILE = ETL_PATH + 'landslides.csv'
TSUNAMI_FILE = ETL_PATH + 'tsunamis.csv'
HURRICANES_FILE = ETL_PATH + 'hurricanes.csv'
CITIES_JSON_FILE = ETL_PATH + 'cities.json'
STATES_JSON_FILE = ETL_PATH + 'states.json'
DISASTERS_JSON_FILE = ETL_PATH + 'disasters.json'

# Potential ones to work on
WILDFIRES_DATASET = 'rtatman/188-million-us-wildfires'
WILDFIRES_FILE = 'FPA_FOD_20170508.sqlite'
VOLCANO_DATASET = 'smithsonian/volcanic-eruptions'
VOLCANO_FILE = 'eruptions.csv'


def save_json(filename: str, data: dict):
    """Save data into JSON file"""
    if not isinstance(data, dict):
        raise ValueError(f'Bad type for data: {type(data)}')
    os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


def load_json(filename: str) -> dict:
    """Load Python dictionary from JSON file"""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"JSON file not found: {filename=}")
    with open(filename, 'r') as f:
        return json.load(f)


def is_json_populated(filename: str) -> bool:
    """
    Check if a JSON file exists and contains non-empty data.

    Args:
        filename: Path to the JSON file

    Returns:
        True if file exists and contains data (non-empty dict/list)
        False otherwise
    """
    if not os.path.exists(filename):
        return False

    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return len(data) > 0
            elif isinstance(data, list):
                return len(data) > 0
            else:
                return False
    except (json.JSONDecodeError, IOError):
        return False


def main():
    # Clear database
    print("Clearing database")
    num_deleted = clear_db()
    print(f"Deleted: {num_deleted}")

    # Seed nations
    print("Seeding nations...")
    seed_nations(NATIONS_FILE)

    # Seed coordinates
    print("Seeding coordinates...")
    if not is_json_populated(scd.COORDS_FILE):
        scd.seed_coords(EARTHQUAKES_FILE, 'latitude', 'longitude')
        scd.seed_coords(LANDSLIDE_FILE, 'latitude', 'longitude')
        scd.seed_coords(TSUNAMI_FILE, 'LATITUDE', 'LONGITUDE')

    # Seed records from coordinates
    if is_json_populated(scd.COORDS_FILE):
        print("Seeding cities")
        sct.seed_cities(scd.COORDS_FILE)
        print("Seeding states")
        ss.seed_states(scd.COORDS_FILE)
        print("Seeding disasters")
        sd.seed_disasters(EARTHQUAKES_FILE, nd.EARTHQUAKE)
        sd.seed_disasters(LANDSLIDE_FILE, nd.LANDSLIDE)
        sd.seed_disasters(TSUNAMI_FILE, nd.TSUNAMI)
        # TODO: upload hurricane file
        # sd.seed_disasters(HURRICANES_FILE, nd.HURRICANE)

    print("Seeding complete")


if __name__ == '__main__':
    main()
