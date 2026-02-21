import os
import csv
import server.controllers.cities as ct
import server.controllers.states as st
import server.controllers.nations as nt
import server.controllers.natural_disasters as nd
from server.etl.geocoding import reverse_geocode
from datetime import datetime


def extract(filename: str) -> list:
    """Extract disaster data from its CSV file"""
    try:
        with open(filename, mode='r', encoding='utf-8') as f:
            extracted = csv.DictReader(f)
            return list(extracted)
    except Exception as e:
        print(f'Problem reading csv file: {str(e)}')
        exit(1)


def transform_date(year: str, month: str, day: str) -> str:
    return (f"{int(float(year or 1)):04d}"
            f"-{int(float(month or 1)):02d}"
            f"-{int(float(day or 1)):02d}") 


def transform_earthquake(row: dict) -> list:
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

        loc_data = load_location(lat, lon)
        return {
            nd.NAME: f"Earthquake at {loc_data['city_name']}",
            nd.DISASTER_TYPE: nd.EARTHQUAKE,
            nd.DATE: date,
            nd.LATITUDE: lat,
            nd.LONGITUDE: lon,
            nd.DESCRIPTION: f"Magnitude: {row.get('mag', 'N/A')},"
                            f"Depth: {row.get('depth', 'N/A')} km"
        }
    except Exception as e:
        print(e)


def transform_landslide(row: dict) -> list:
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

        loc_data = load_location(lat, lon)
        return {
            nd.NAME: f"Landslide at {loc_data['city_name']}",
            nd.DISASTER_TYPE: nd.LANDSLIDE,
            nd.DATE: date,
            nd.LATITUDE: lat,
            nd.LONGITUDE: lon,
            nd.DESCRIPTION: f"Size: {size}, Trigger: {trigger}"
        }
    except Exception as e:
        print(e)


def transform_tsunami(row: dict) -> list:
    """Transform tsunami data into format CRUD API can understand"""
    try:
        if not isinstance(row, dict):
            raise ValueError(f'Bad type for row: {type(row)}')
        lat = float(row['LATITUDE'])
        lon = float(row['LONGITUDE'])

        date = transform_date(row.get('YEAR'), row.get('MONTH'), row.get('DAY'))
        # Skip negative years
        if date[0] == '-':
            return None

        loc_data = load_location(lat, lon)
        return {
            nd.NAME: f"Tsunami at {loc_data['city_name']}",
            nd.DISASTER_TYPE: nd.TSUNAMI,
            nd.DATE: date,
            nd.LATITUDE: lat,
            nd.LONGITUDE: lon,
        }
    except Exception as e:
        print(e)


def transform_hurricane(row: dict) -> list:
    """Transform hurricane data into format CRUD API can understand"""
    try:
        if not isinstance(row, dict):
            raise ValueError(f'Bad type for row: {type(row)}')
        lat = float(row.get('latitude', 0))
        lon = float(row.get('longitude', 0))
        loc_data = load_location(lat, lon)
        wind_speed = row.get('wind_speed', 'N/A')
        category = row.get('category', 'N/A')
        return {
            nd.NAME: f"Hurricane at {loc_data['city_name']}",
            nd.DISASTER_TYPE: nd.HURRICANE,
            nd.DATE: row.get('date', ''),
            nd.LATITUDE: lat,
            nd.LONGITUDE: lon,
            nd.DESCRIPTION: f"Category: {category}, Wind Speed: {wind_speed} mph"
        }
    except Exception as e:
        print(e)


def load_location(lat: float, lon: float):
    """
    Use reverse geocoding to resolve coordinates into nation, state, city.

    Args:
        lat (float): Latitude (-90 to 90)
        lon (float): Longitude (-180 to 180)

    Returns:
        dict: Dictionary containing created IDs and location names

    Raises:
        ValueError: If coordinates are invalid or city cannot be found
        ConnectionError: If geocoding service is unavailable
    """
    # Validate coordinates
    if not (-90 <= lat <= 90):
        raise ValueError(f"latitude not between -90 and 90: {lat}.")
    if not (-180 <= lon <= 180):
        raise ValueError(f"longitude not between -180 and 180: {lon}.")

    # Attempt reverse geocoding with error handling
    try:
        loc = reverse_geocode(lat, lon)
    except Exception as e:
        raise ConnectionError(f"Geocoding failed for ({lat}, {lon}): {e}")

    city_name = loc.get('city')
    state_name = loc.get('state')
    nation_name = loc.get('country')
    nation_code = loc.get('country_code')

    if not city_name:
        raise ValueError(f"No city found for coordinates ({lat}, {lon})")

    # Create nation (if provided)
    if nation_name:
        try:
            nt.nations.create({
                nt.CODE: nation_code,
                nt.NAME: nation_name
            })
        except Exception as e:
            print(f"Warning: Failed to create nation '{nation_name}': {e}")

    # Create state (if provided)
    if state_name and nation_name:
        try:
            st.states.create({
                st.NAME: state_name,
                st.NATION_NAME: nation_name
            })
            print(f"Created state: {state_name}, {nation_name}")
        except Exception as e:
            print(f"Warning: Failed to create state '{state_name}': {e}")

    # Create city
    if city_name and state_name:
        try:
            ct.cities.create({
                ct.NAME: city_name,
                ct.STATE_NAME: state_name,
                ct.NATION_NAME: nation_name,
                ct.LATITUDE: lat,
                ct.LONGITUDE: lon,
            })
            print(f"Created city: {city_name} ({state_name}, {nation_name})")
        except Exception as e:
            print(f"Warning: Failed to create city '{city_name}': {e}")

    return {
        'city_name': city_name,
        'state_name': state_name,
        'nation_name': nation_name,
    }


def load_disaster(transformed: list):
    """Load a disaster into database"""
    try:
        _id = nd.disasters.create(transformed)
        print(f"Created disaster: {_id}")
    except Exception as e:
        print("Warning could not create disaster: ", e)


def seed_disasters(filename: str, disaster_type: str):
    """Main seed function to be exported"""
    # Get the right transformation function
    transforms = {
        nd.EARTHQUAKE: transform_earthquake,
        nd.LANDSLIDE: transform_landslide,
        nd.TSUNAMI: transform_tsunami,
        nd.HURRICANE: transform_hurricane,
    }
    if disaster_type not in transforms:
        raise ValueError(f'Unrecognized disaster_type: {disaster_type}')

    # Perform ETL operations
    rows = extract(filename)
    transform_func = transforms[disaster_type]
    for row in rows:
        transformed = transform_func(row)
        if transformed is not None:
            load_disaster(transformed)