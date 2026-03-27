"""
ETL script for seeding natural disaster data
"""

import server.etl.common as common
import server.controllers.natural_disasters as nd
from server.controllers.geocoding import reverse_geocode
from datetime import datetime


def transform_date(year: str, month: str, day: str) -> str:
    return (f"{int(float(year or 1)):04d}"
            f"-{int(float(month or 1)):02d}"
            f"-{int(float(day or 1)):02d}")


def transform_earthquake(row: dict) -> dict:
    """Transform earthquake data into format CRUD API can understand"""
    try:
        if not isinstance(row, dict):
            raise ValueError(f'Bad type for row: {type(row)}')
        lat = float(row['latitude'])
        lon = float(row['longitude'])

        day, month, year = row.get('date_time').split(' ')[0].split('-')
        date = transform_date(year, month, day)
        # Skip negative years
        if date[0] == '-':
            return None

        return {
            nd.NAME: f"Earthquake {row.get('title')}",
            nd.DISASTER_TYPE: nd.EARTHQUAKE,
            nd.DATE: date,
            nd.LATITUDE: lat,
            nd.LONGITUDE: lon,
            nd.DESCRIPTION: f"Magnitude: {row.get('mag', 'N/A')}, "
                            f"Depth: {row.get('depth', 'N/A')} km"
        }
    except Exception as e:
        print(e)


def transform_landslide(row: dict) -> dict:
    """Transform landslide data into format CRUD API can understand"""
    try:
        if not isinstance(row, dict):
            raise ValueError(f'Bad type for row: {type(row)}')
        lat = float(row['latitude'])
        lon = float(row['longitude'])
        size = row.get('landslide_size', 'N/A')
        trigger = row.get('trigger', 'N/A')

        month, day, year = row.get('event_date').split(' ')[0].split('/')
        date = transform_date(year, month, day)
        # Skip negative years
        if date[0] == '-':
            return None

        return {
            nd.NAME: f"Landslide at {row.get('event_title')}",
            nd.DISASTER_TYPE: nd.LANDSLIDE,
            nd.DATE: date,
            nd.LATITUDE: lat,
            nd.LONGITUDE: lon,
            nd.DESCRIPTION: f"Size: {size}, Trigger: {trigger}"
        }
    except Exception as e:
        print(e)


def transform_tsunami(row: dict) -> dict:
    """Transform tsunami data into format CRUD API can understand"""
    try:
        if not isinstance(row, dict):
            raise ValueError(f'Bad type for row: {type(row)}')
        lat = float(row['LATITUDE'])
        lon = float(row['LONGITUDE'])
        # Default to '01' if field is an empty string
        date = transform_date(row.get('YEAR'), row.get('MONTH'), row.get('DAY'))
        # Skip negative years
        if date[0] == '-':
            return None

        return {
            nd.NAME: f"Tsunami at {row.get('LOCATION_NAME')}",
            nd.DISASTER_TYPE: nd.TSUNAMI,
            nd.DATE: date,
            nd.LATITUDE: lat,
            nd.LONGITUDE: lon,
            nd.DESCRIPTION: f"{row.get('COMMENTS', '')}"
        }
    except Exception as e:
        print(e)


def transform_hurricane(row: dict) -> dict:
    """Transform hurricane data into format CRUD API can understand"""
    try:
        if not isinstance(row, dict):
            raise ValueError(f'Bad type for row: {type(row)}')
        lat = float(row.get('latitude', 0))
        lon = float(row.get('longitude', 0))
        wind_speed = row.get('wind_speed', 'N/A')
        category = row.get('category', 'N/A')
        return {
            nd.NAME: f"Hurricane at {city_name}",
            nd.DISASTER_TYPE: nd.HURRICANE,
            nd.DATE: row.get('date', ''),
            nd.LATITUDE: lat,
            nd.LONGITUDE: lon,
            nd.DESCRIPTION: f"Category: {category}, Wind Speed: {wind_speed} mph"
        }
    except Exception as e:
        print(e)


def seed_disasters(disaster_file: str, disaster_type: str):
    """Seed disasters for the given disaster type"""
    transforms = {
        nd.EARTHQUAKE: transform_earthquake,
        nd.LANDSLIDE: transform_landslide,
        nd.TSUNAMI: transform_tsunami,
        nd.HURRICANE: transform_hurricane,
    }
    if disaster_type not in transforms:
        raise ValueError(f'Unrecognized disaster_type: {disaster_type}')

    rows = common.extract_csv(disaster_file)
    transform_func = transforms[disaster_type]
    transformed = []
    seen = []
    for row in rows:
        new_record = transform_func(row)
        if new_record is not None:
            # Add fields common to all disasters
            new_record.update({
                'show': True,
                'reports': [],
                'parent_event': None,
                'severity': None,
            })
            # Add transformed disaster to list if it is not a duplicate
            if not nd.disasters.find_duplicate(new_record, search_list=seen):
                seen.append(new_record)
                transformed.append(new_record)
    common.load(nd.disasters, transformed)


if __name__ == '__main__':
    seed_disasters(common.EARTHQUAKES_FILE, nd.EARTHQUAKE)
    seed_disasters(common.LANDSLIDE_FILE, nd.LANDSLIDE)
    seed_disasters(common.TSUNAMI_FILE, nd.TSUNAMI)
    # TODO: upload hurricane file
    # seed_disasters(common.HURRICANES_FILE, nd.HURRICANE)
