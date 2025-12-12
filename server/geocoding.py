"""
Geocoding API endpoint.
"""
from flask import request
from flask_restx import Resource, Namespace, fields
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from server.etl.geocoding import reverse_geocode

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
