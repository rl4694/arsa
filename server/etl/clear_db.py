"""
This script clears the database

You can run this script with: `python -m server.etl.clear_db`
"""

import server.controllers.cities as ct
import server.controllers.states as st
import server.controllers.nations as nt
import server.controllers.natural_disasters as nd
import data.db_connect as dbc

def clear_db():
    num_deleted = 0
    num_deleted += dbc.delete(ct.cities.collection, {})
    num_deleted += dbc.delete(st.states.collection, {})
    num_deleted += dbc.delete(nt.nations.collection, {})
    num_deleted += dbc.delete(nd.disasters.collection, {})
    return num_deleted

if __name__ == '__main__':
    num_deleted = clear_db()
    print(num_deleted)
