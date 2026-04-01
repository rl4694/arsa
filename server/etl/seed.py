"""
This script seeds our data with data from various APIs.

You can run this script with: `python -m server.etl.seed`
"""

import os
import json
import server.controllers.cities as ct
import server.controllers.states as st
import server.controllers.nations as nt
import server.controllers.natural_disasters as nd
import server.etl.common as common
from server.etl.clear_db import clear_db
from server.etl.seed_disasters import seed_disasters
from server.etl.seed_coords import seed_coords
from server.etl.seed_nations import seed_nations
from server.etl.seed_cities import seed_cities
from server.etl.seed_states import seed_states


def main():
    # Clear database
    print("Clearing database...")
    num_deleted = clear_db()
    print(f"Deleted: {num_deleted}")

    # Seed nations
    print("Seeding nations...")
    seed_nations(common.NATIONS_FILE)

    # Seed coordinates
    print("Seeding coordinates...")
    if not common.is_json_populated(common.COORDS_FILE):
        for config in common.COORDS_CONFIG:
            seed_coords(config[0], config[1], config[2])

    # Seed records from coordinates
    if common.is_json_populated(common.COORDS_FILE):
        print("Seeding cities...")
        seed_cities(common.COORDS_FILE)

        print("Seeding states...")
        seed_states(common.COORDS_FILE)

        print("Seeding disasters...")
        seed_disasters(common.EARTHQUAKES_FILE, nd.EARTHQUAKE)
        seed_disasters(common.LANDSLIDE_FILE, nd.LANDSLIDE)
        seed_disasters(common.TSUNAMI_FILE, nd.TSUNAMI)
        seed_disasters(common.HURRICANES_FILE, nd.HURRICANE)

    print("Seeding complete")


if __name__ == '__main__':
    main()
