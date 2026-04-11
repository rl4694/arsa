"""
This script batch updates records in the database. It is used to add, remove,
and modify fields when we want to keep all existing data rather than clearing
and reseeding the database.

You can run this script with: `python -m server.etl.backfill`
"""
import server.controllers.natural_disasters as nd
import data.db_connect as dbc
from pprint import pprint

# Collection to operate on
CRUD = nd.disasters

# Fields to modify in the format: ( field_name, default_value )
NEW_FIELDS = [
    ('show', True),
    ('reports', []),
    ('parent_event', None),
    ('severity', None),
]

for field, default in NEW_FIELDS:
    dbc.update(CRUD.collection, {field: {"$exists": False}}, {field: default})
pprint(CRUD.read())