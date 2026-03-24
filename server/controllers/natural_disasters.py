"""
This file implements CRUD operations for natural disasters.
"""

from flask import request
from flask_restx import Resource, Namespace, fields
from server.controllers.crud import CRUD
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from numbers import Real
import re

DISASTERS_RESP = 'records'
COLLECTION = 'natural_disasters'
NAME = 'name'
DISASTER_TYPE = 'type'
DATE = 'date'
LATITUDE = 'latitude'
LONGITUDE = 'longitude'
DESCRIPTION = 'description'

# New Optional Fields:
SEVERITY = 'severity'
SHOW = 'show'
PARENT_EVENT = 'parent_event'
REPORTS = 'reports'

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
        LATITUDE: Real,
        LONGITUDE: Real,
        DESCRIPTION: str,
        SEVERITY: Real,
        SHOW: bool,
        PARENT_EVENT: str,
        REPORTS: list,
    }
)


api = Namespace('natural_disasters', description='Natural Disasters CRUD operations')
disaster_model = api.model('NaturalDisaster', {
  NAME: fields.String(required=True),
  DISASTER_TYPE: fields.String(required=True),
  DATE: fields.String(required=True, default=datetime.now().strftime("%Y-%m-%d")),
  LATITUDE: fields.Float(required=True, default=0.5),
  LONGITUDE: fields.Float(required=True, default=0.5),
  DESCRIPTION: fields.String(),
  SEVERITY: fields.Float(),
  SHOW: fields.Boolean(default=True),
  PARENT_EVENT: fields.String(),
  REPORTS: fields.List(fields.String())
})


@api.route('/', strict_slashes=False)
class DisasterList(Resource):
    @api.doc('list_disasters',
             params={
                 'date': 'Return disasters occurring on this date (YYYY-MM-DD)',
                 'start_date': 'Return disasters after this date (YYYY-MM-DD)',
                 'end_date': 'Return disasters before this date (YYYY-MM-DD)'
             })
    def get(self):
        """Get natural disasters optionally filtered by date."""

        # date = request.args.get('date')
        # start_date = request.args.get('start_date')
        # end_date = request.args.get('end_date')

        # records = disasters.read()

        # filtered = [r for r in records.values() if r.get(SHOW, True)]

        # if date:
        #     validate_date(date)
        #     filtered = [r for r in filtered if r.get(DATE) == date]

        # if start_date:
        #     validate_date(start_date)
        #     filtered = [r for r in filtered if r.get(DATE) and r.get(DATE) >= start_date]

        # if end_date:
        #     validate_date(end_date)
        #     filtered = [r for r in filtered if r.get(DATE) and r.get(DATE) <= end_date]
        return {DISASTERS_RESP: disasters.read()}

    @api.expect(disaster_model)
    @api.doc('create_disaster')
    def post(self):
        """Create a new natural disaster."""
        data = request.json
        data.setdefault(SHOW, True)
        data.setdefault(PARENT_EVENT, None)
        data.setdefault(REPORTS, [])
        data.setdefault(SEVERITY, None)
        _id = disasters.create(data)
        created = disasters.select(_id)
        return {DISASTERS_RESP: created}, 201


@api.route('/<string:disaster_id>')
class Disaster(Resource):
    @api.doc('get_disaster')
    def get(self, disaster_id):
        """Get a specific disaster by ID."""
        record = disasters.select(disaster_id)
        return {DISASTERS_RESP: record}

    @api.expect(disaster_model)
    @api.doc('update_disaster')
    def put(self, disaster_id):
        """Update an existing disaster."""
        disasters.update(disaster_id, request.json)
        record = disasters.select(disaster_id)
        return {DISASTERS_RESP: record}

    @api.doc('delete_disaster')
    def delete(self, disaster_id):
        """Delete a disaster by ID."""
        disasters.delete(disaster_id)
        return '', 204
        
# New Endpoints to Support Reports        

@api.route('/<string:event_id>/reports')
class DisasterReports(Resource):

    def get(self, event_id):
        event = disasters.select(event_id)

        report_ids = event.get(REPORTS, [])

        results = []
        for rid in report_ids:
            try:
                results.append(disasters.select(rid))
            except Exception:
                continue

        return {"reports": results}
        
@api.route('/<string:event_id>/reports/<string:report_id>')
class LinkReport(Resource):

    def post(self, event_id, report_id):

        event = disasters.select(event_id)
        report = disasters.select(report_id)

        reports = event.get(REPORTS, [])
        if report_id not in reports:
            reports.append(report_id)

        disasters.update(event_id, {REPORTS: reports})

        disasters.update(report_id, {
            SHOW: False,
            PARENT_EVENT: event_id
        })

        return {"message": "linked"}
        
# for search by radius
# this calculates great circle distance to help us consolidate
# nearby events time and space wise

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c
    
@api.route('/search')
class DisasterSearch(Resource):

    @api.doc('search_disasters',
             params={
                 'lat': 'Latitude',
                 'lon': 'Longitude',
                 'radius_km': 'Search radius in km (default 100)',
                 'date_start': 'Start date (YYYY-MM-DD)',
                 'date_end': 'End date (YYYY-MM-DD)',
                 'type': 'Disaster type'
             })
    def get(self):
        """Search for nearby disasters (used for duplicate detection)."""

        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius_km', type=float, default=100)

        date_start = request.args.get('date_start')
        date_end = request.args.get('date_end')
        disaster_type = request.args.get('type')

        records = disasters.read().values()

        results = []

        for r in records:

            # Optional: include hidden reports too for dedupe
            # (remove SHOW filter intentionally)

            if disaster_type and r.get(DISASTER_TYPE) != disaster_type:
                continue

            if date_start:
                validate_date(date_start)
                if not r.get(DATE) or r.get(DATE) < date_start:
                    continue

            if date_end:
                validate_date(date_end)
                if not r.get(DATE) or r.get(DATE) > date_end:
                    continue

            if lat is not None and lon is not None:

                if r.get(LATITUDE) is None or r.get(LONGITUDE) is None:
                    continue

                dist = haversine(
                    lat,
                    lon,
                    r.get(LATITUDE),
                    r.get(LONGITUDE)
                )

                if dist > radius:
                    continue

            results.append(r)

        return {DISASTERS_RESP: results}
