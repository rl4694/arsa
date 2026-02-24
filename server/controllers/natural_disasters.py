"""
This file implements CRUD operations for natural disasters.
"""

from flask import request
from flask_restx import Resource, Namespace, fields
from server.controllers.crud import CRUD
from datetime import datetime
import re

DISASTERS_RESP = 'records'
COLLECTION = 'natural_disasters'
NAME = 'name'
DISASTER_TYPE = 'type'
DATE = 'date'
LATITUDE = 'latitude'
LONGITUDE = 'longitude'
DESCRIPTION = 'description'

EARTHQUAKE = 'earthquake'
LANDSLIDE = 'landslide'
TSUNAMI = 'tsunami'
HURRICANE = 'hurricane'
DISASTER_TYPES = [EARTHQUAKE, LANDSLIDE, TSUNAMI, HURRICANE]
KEY = (NAME, DATE, LATITUDE, LONGITUDE)

def validate_date(date_string: str) -> None:
    """
    Validate date string in format 'yyyy-mm-dd' or '-yyyy-mm-dd' (for negative/BCE years).
    Supports 3-digit years (e.g., '500-01-01') and negative years (e.g., '-500-01-01').
    
    Args:
        date_string: Date string to validate
        
    Raises:
        ValueError: If date format is invalid or values are out of range
    """
    # Pattern: optional minus sign, 1-4 digits for year, month, day
    pattern = r'^(-?)(\d{1,4})-(\d{1,2})-(\d{1,2})$'
    match = re.match(pattern, date_string)
    
    if not match:
        raise ValueError(f'Invalid date format: {date_string}. Expected format: yyyy-mm-dd or -yyyy-mm-dd')
    
    negative, year_str, month_str, day_str = match.groups()
    
    try:
        year = int(year_str)
        month = int(month_str)
        day = int(day_str)
        
        # Apply negative sign if present
        if negative:
            year = -year
        
        # Validate ranges
        if month < 1 or month > 12:
            raise ValueError(f'Month must be between 1 and 12, got {month}')
        
        if day < 1 or day > 31:
            raise ValueError(f'Day must be between 1 and 31, got {day}')
        
        # For positive years only, try to validate with datetime
        # (datetime only supports years 1-9999)
        if year > 0 and year <= 9999:
            try:
                datetime(year, month, day)
            except ValueError as e:
                raise ValueError(f'Invalid date: {date_string} - {str(e)}')
    except ValueError as e:
        raise ValueError(f'Invalid date string: {date_string} - {str(e)}')


class NaturalDisasters(CRUD):
    def validate(self, fields: dict):
        super().validate(fields)
        # Check if date is in the format 'yyyy-mm-dd' or '-yyyy-mm-dd'
        if DATE in fields:
            validate_date(fields[DATE])

disasters = NaturalDisasters(
    COLLECTION,
    KEY,
    {
        NAME: str,
        DISASTER_TYPE: str,
        DATE: str,
        LATITUDE: float,
        LONGITUDE: float,
        DESCRIPTION: str,
    }
)


api = Namespace('natural_disasters', description='Natural Disasters CRUD operations')
disaster_model = api.model('NaturalDisaster', {
  NAME: fields.String(required=True),
  DISASTER_TYPE: fields.String(required=True),
  DATE: fields.String(required=True, default=datetime.now().strftime("%Y-%m-%d")),
  LATITUDE: fields.Float(required=True, default=0.5),
  LONGITUDE: fields.Float(required=True, default=0.5),
  DESCRIPTION: fields.String()
})


@api.route('/')
class DisasterList(Resource):
    @api.doc('list_disasters')
    def get(self):
        """Get all natural disasters."""
        return {DISASTERS_RESP: disasters.read()}

    @api.expect(disaster_model)
    @api.doc('create_disaster')
    def post(self):
        """Create a new natural disaster."""
        data = request.json
        _id = disasters.create(data)
        created = disasters.select(_id)
        return {DISASTERS_RESP: created}, 201


@api.route('/<string:disaster_id>')
class Disaster(Resource):
    @api.doc('get_disaster')
    def get(self, disaster_id):
        """Get a specific disaster by ID."""
        try:
            record = disasters.select(disaster_id)
            return {DISASTERS_RESP: record}
        except Exception:
            api.abort(404, "Disaster not found")

    @api.expect(disaster_model)
    @api.doc('update_disaster')
    def put(self, disaster_id):
        """Update an existing disaster."""
        try:
            disasters.update(disaster_id, request.json)
            record = disasters.select(disaster_id)
            return {DISASTERS_RESP: record}
        except KeyError:
            api.abort(404, "Disaster not found")
        except Exception:
            api.abort(400, "Bad request")

    @api.doc('delete_disaster')
    def delete(self, disaster_id):
        """Delete a disaster by ID."""
        try:
            disasters.delete(disaster_id)
            return '', 204
        except KeyError:
            api.abort(404, "Disaster not found")
        except Exception:
            api.abort(400, "Bad request")
