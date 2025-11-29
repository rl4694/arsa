"""
Geocoding module for converting coordinates to location data.
Uses OpenStreetMap Nominatim service via geopy.
"""
import math
from flask import request
from flask_restx import Resource, Namespace, fields
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from geopy.extra.rate_limiter import RateLimiter

# Initialize geocoder with a user agent (required by Nominatim)
geolocator = Nominatim(user_agent="geodata-app")
_reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1.0,
                       max_retries=1)

# Create namespace for geocoding endpoints
api = Namespace('geocode', description='Geocoding operations')

# Response model
location_model = api.model('Location', {
    'city': fields.String(description='City name'),
    'state': fields.String(description='State/Province name'),
    'country': fields.String(description='Country name'),
    'latitude': fields.Float(description='Latitude'),
    'longitude': fields.Float(description='Longitude'),
    'display_name': fields.String(description='Full address')
})


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
        location = _reverse((lat, lon), language="en")

        # Increase search radius if not found
        if location is None:
            for search_km in (1, 5, 20, 50, 100):
                # make fix relating to curvature away from equator
                # more accurate latitude measurements
                dlat = search_km / 110.574
                cos_lat = math.cos(math.radians(lat))
                if abs(cos_lat) < 0.01:   # account for poles
                    cos_lat = 0.01
                dlon = search_km / (111.320 * cos_lat)

                candidates = [
                    (lat + dlat, lon), (lat - dlat, lon),
                    (lat, lon + dlon), (lat, lon - dlon),
                    (lat + dlat, lon + dlon), (lat + dlat, lon - dlon),
                    (lat - dlat, lon + dlon), (lat - dlat, lon - dlon),
                ]
                for clat, clon in candidates:
                    if -90 <= clat <= 90 and -180 <= clon <= 180:
                        location = _reverse((clat, clon), language="en")
                        if location is not None:
                            break
                if location is not None:
                    break

        if location is None:
            return {
                'city': None,
                'state': None,
                'country': None,
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

        return {
            'city': city,
            'state': state,
            'country': country,
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


# API ENDPOINT
@api.route('/')
class GeocodeResource(Resource):
    @api.doc('reverse_geocode',
             params={
                 'lat': 'Latitude (required, between -90 and 90)',
                 'lon': 'Longitude (required, between -180 and 180)'
             })
    @api.response(200, 'Success', location_model)
    @api.response(400, 'Bad Request - Invalid or missing parameters')
    @api.response(503, 'Service Unavailable - Geocoding service error')
    def get(self):
        """
        Convert coordinates to location information.

        Query parameters:
        - lat: Latitude (required)
        - lon: Longitude (required)

        Example: /geocode?lat=40.7128&lon=-74.0060
        """
        # Get query parameters
        lat_str = request.args.get('lat')
        lon_str = request.args.get('lon')

        # Validate required parameters
        if lat_str is None or lon_str is None:
            api.abort(400, "Both 'lat' and 'lon' parameters are required")

        # Convert to float
        try:
            lat = float(lat_str)
            lon = float(lon_str)
        except ValueError:
            api.abort(400, "Latitude and longitude must be valid numbers")

        # Perform reverse geocoding
        try:
            result = reverse_geocode(lat, lon)
            return result, 200
        except ValueError as e:
            api.abort(400, str(e))
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            api.abort(503, str(e))
