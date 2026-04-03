"""
Common functions and constants for ETL scripts
"""

import json
import csv
import os
from server.controllers.crud import CRUD


# Initialize constants
ETL_PATH = 'server/etl/'
NATIONS_FILE = ETL_PATH + 'nations.csv'
EARTHQUAKES_FILE = ETL_PATH + 'earthquakes.csv'
LANDSLIDE_FILE = ETL_PATH + 'landslides.csv'
TSUNAMI_FILE = ETL_PATH + 'tsunamis.csv'
HURRICANES_FILE = ETL_PATH + 'hurricanes.csv'
COORDS_FILE = ETL_PATH + 'coords.json'
COORDS_CONFIG = [
    (EARTHQUAKES_FILE, 'latitude', 'longitude'),
    (LANDSLIDE_FILE, 'latitude', 'longitude'),
    (TSUNAMI_FILE, 'LATITUDE', 'LONGITUDE'),
    (HURRICANES_FILE, 'latitude', 'longitude'),
]

# Potential datasets to work on
WILDFIRES_DATASET = 'rtatman/188-million-us-wildfires'
WILDFIRES_FILE = 'FPA_FOD_20170508.sqlite'
VOLCANO_DATASET = 'smithsonian/volcanic-eruptions'
VOLCANO_FILE = 'eruptions.csv'


def is_json_populated(filename: str) -> bool:
    """
    Check if a JSON file exists and contains non-empty data.
    """
    if not os.path.exists(filename):
        return False

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return len(data) > 0
            elif isinstance(data, list):
                return len(data) > 0
            else:
                return False
    except (json.JSONDecodeError, IOError):
        return False


def extract_json(filename: str, **kwargs) -> dict:
    """Extract data from JSON file"""
    with open(filename, mode='r', encoding='utf-8') as f:
        return json.load(f, **kwargs)


def extract_csv(filename: str, **kwargs) -> list:
    """Extract data from CSV file"""
    with open(filename, mode='r', encoding='utf-8') as f:
        return list(csv.DictReader(f, **kwargs))


def load(crud: CRUD, transformed: list):
    """Load transformed data into database using CRUD operations"""
    try:
        crud.create_many(transformed)
    except Exception as e:
        print(f"Failed to create {crud.collection}: {e}")
