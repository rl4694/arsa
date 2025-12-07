"""
This script seeds our data with data from various APIs.

You can run this script with: `python3 server/etl/seed.py`
Be sure to empty your database before running this file.
"""

import os
import csv
import server.controllers.cities as ct
import server.controllers.states as st
import server.controllers.nations as nt
import server.controllers.natural_disasters as nd
from server.common import is_json_populated, save_json
from server.geocoding import reverse_geocode
from server.etl.seed_nations import seed_nations
import server.etl.seed_disasters as sd


# Initialize constants
ETL_PATH = 'server/etl/'
NATIONS_FILE = ETL_PATH + 'nations.csv'
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


def main():
    print("Seeding nations...")
    seed_nations(NATIONS_FILE)

    if not (
        is_json_populated(CITIES_JSON_FILE) and
        is_json_populated(STATES_JSON_FILE) and
        is_json_populated(DISASTERS_JSON_FILE)
    ):
        print("Seeding disaster data...")
        sd.seed_disasters(EARTHQUAKES_FILE, sd.EARTHQUAKE)
        sd.seed_disasters(LANDSLIDE_FILE, sd.LANDSLIDE)
        sd.seed_disasters(TSUNAMI_FILE, sd.TSUNAMI)

    # Save to JSON files
    try:
        save_json(CITIES_JSON_FILE, ct.cities.read())
        save_json(STATES_JSON_FILE, st.states.read())
        save_json(DISASTERS_JSON_FILE, nd.disasters.read())
    except Exception as e:
        print(f"Warning: Could not save to JSON: {e}")

    print("Seeding complete")


if __name__ == '__main__':
    main()
