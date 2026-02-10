"""
Geocoding utilities for converting coordinates to location data.
Uses OpenStreetMap Nominatim service via geopy.
"""
import math
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from geopy.extra.rate_limiter import RateLimiter

# Initialize geocoder with a user agent (required by Nominatim)
geolocator = Nominatim(user_agent="geodata-app")
reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1.0, max_retries=1)
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.0, max_retries=1)
SEARCH_KM = 100


def reverse_geocode(lat: float, lon: float) -> dict:
    """
    Convert coordinates to city, state, country information.

    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)

    Returns:
        dict with keys: city, state, country, display_name

    Raises:
        ValueError: If coordinates are invalid
        GeocoderTimedOut: If the service times out
        GeocoderServiceError: If the service fails
    """
    # Validate coordinates
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        raise ValueError("Latitude and longitude must be numbers")

    if not -90 <= lat <= 90:
        raise ValueError(f"Latitude must be between -90 and 90, got {lat}")

    if not -180 <= lon <= 180:
        raise ValueError(f"Longitude must be between -180 and 180, got {lon}")

    try:
        # Reverse geocode the coordinates
        location = reverse((lat, lon), language="en")

        # Increase search radius if not found
        if location is None or 'city' not in location.raw.get('address', {}):
            # make fix relating to curvature away from equator
            # more accurate latitude measurements
            dlat = SEARCH_KM / 110.574
            cos_lat = math.cos(math.radians(lat))
            if abs(cos_lat) < 0.01:   # account for poles
                cos_lat = 0.01
            dlon = SEARCH_KM / (111.320 * cos_lat)

            viewbox = [
                max(lat - dlat, -90),
                max(lon - dlon, -180),
                min(lat + dlat, 90),
                min(lon + dlon, 180),
            ]
            location = geocode(
                query="city",
                bounded=True,
                viewbox=[(viewbox[0], viewbox[1]), (viewbox[2], viewbox[3])],
                addressdetails=True,
            )

        if location is None:
            return {
                'city': None,
                'state': None,
                'country': None,
                'country_code': None,
                'latitude': lat,
                'longitude': lon,
                'display_name': 'Location not found'
            }

        # Extract address components
        address = location.raw.get('address', {})

        # Try multiple fields for city (different places use different keys)
        city = (address.get('city') or
                address.get('town') or
                address.get('village') or
                address.get('hamlet') or
                address.get('municipality'))

        # Try multiple fields for state
        state = (address.get('state') or
                 address.get('province') or
                 address.get('region'))

        country = address.get('country')
        country_code = address.get('country_code')

        return {
            'city': city,
            'state': state,
            'country': country,
            'country_code': country_code,
            'latitude': lat,
            'longitude': lon,
            'display_name': location.address
        }

    except GeocoderTimedOut:
        raise GeocoderTimedOut(
            "The geocoding service timed out. Please try again."
        )
    except GeocoderServiceError as e:
        raise GeocoderServiceError(f"Geocoding service error: {str(e)}")


def forward_geocode(query: str):
    """
    Convert a place query string to latitude/longitude using Nominatim.

    Args:
        query: Free-text query like "Boise, Idaho, United States".

    Returns:
        (lat, lon) as floats, or (None, None) if not found.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string")

    location = geocode(query, language="en", addressdetails=True)
    if location is None:
        return None, None

    return float(location.latitude), float(location.longitude)
