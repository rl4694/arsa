"""
All interaction with MongoDB should be through this file!
We may be required to use a new database at any point.
"""
import os
from functools import wraps
from dotenv import load_dotenv
import pymongo as pm
import certifi

load_dotenv()

LOCAL = "0"
CLOUD = "1"
SE_DB = 'seDB'
client = None
MONGO_ID = '_id'

CONN_TIMEOUT = 'connectTimeoutMS'
SOCK_TIMEOUT = 'socketTimeoutMS'
CONNECT = 'connect'
MAX_POOL_SIZE = 'maxPoolSize'
PA_SETTINGS = {
    CONN_TIMEOUT: os.getenv('MONGO_CONN_TIMEOUT', 30000),
    SOCK_TIMEOUT: os.getenv('MONGO_SOCK_TIMEOUT', None),
    CONNECT: os.getenv('MONGO_CONNECT', False),
    MAX_POOL_SIZE: os.getenv('MONGO_MAX_POOL_SIZE', 1),
}


def needs_db(func):
    """
    Decorator to ensure database connection before executing function.

    This decorator automatically establishes a database connection
    if one doesn't exist before executing the decorated function.

    Example:
        @needs_db
        def my_function():
            # database connection guaranteed here
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        connect_db()  # This already checks if client is None
        return func(*args, **kwargs)
    return wrapper


def connect_db():
    """
    Connect to MongoDB (either local or cloud based on environment variables).

    Uses CLOUD_MONGO environment variable to determine connection type:
    - CLOUD_MONGO=1: Connect to MongoDB Atlas using MONGO_URL
    - CLOUD_MONGO=0 or unset: Connect to local MongoDB instance

    Returns:
        pymongo.MongoClient: Connected MongoDB client instance

    Raises:
        ValueError: If CLOUD_MONGO=1 but MONGO_URL is not set
    """
    global client
    if client is None:
        print('Setting client because it is None.')
        if os.environ.get('CLOUD_MONGO', LOCAL) == CLOUD:
            mongo_url = os.environ.get('MONGO_URL')
            if not mongo_url:
                raise ValueError('You must set the MONGO_URL env variable '
                                 + 'to use Mongo in the cloud.')
            print('Connecting to Mongo in the cloud.')
            client = pm.MongoClient(mongo_url,
                                    tlsCAFile=certifi.where(),
                                    **PA_SETTINGS)
        else:
            print("Connecting to Mongo locally.")
            client = pm.MongoClient()
    return client


def convert_mongo_id(doc: dict):
    """
    Convert MongoDB ObjectId to string for JSON serialization.

    Args:
        doc (dict): Document containing MongoDB '_id' field

    Note:
        Modifies the document in-place.
    """
    if MONGO_ID in doc:
        # Convert mongo ID to a string so it works as JSON
        if doc and MONGO_ID in doc:
            doc[MONGO_ID] = str(doc[MONGO_ID])


@needs_db
def create(collection, doc, db=SE_DB):
    """
    Insert a single doc into collection.
    """
    return client[db][collection].insert_one(doc)


@needs_db
def read_one(collection, filt, db=SE_DB):
    """
    Find with a filter and return on the first doc found.
    Return None if not found.
    """
    for doc in client[db][collection].find(filt):
        convert_mongo_id(doc)
        return doc
    return None


@needs_db
def delete(collection: str, filt: dict, db=SE_DB):
    """
    Find with a filter and return on the first doc found.
    """
    del_result = client[db][collection].delete_one(filt)
    return del_result.deleted_count


@needs_db
def update(collection, filters, update_dict, db=SE_DB):
    return client[db][collection].update_one(filters, {'$set': update_dict})


@needs_db
def read(collection, db=SE_DB, no_id=True) -> list:
    """
    Returns a list from the db.
    """
    ret = []
    for doc in client[db][collection].find():
        if no_id:
            if MONGO_ID in doc:
                del doc[MONGO_ID]
        else:
            convert_mongo_id(doc)
        ret.append(doc)
    return ret


@needs_db
def read_dict(collection, key, db=SE_DB, no_id=True) -> dict:
    recs = read(collection, db=db, no_id=no_id)
    recs_as_dict = {}
    for rec in recs:
        recs_as_dict[rec[key]] = rec
    return recs_as_dict


@needs_db
def fetch_all_as_dict(key, collection, db=SE_DB):
    ret = {}
    for doc in client[db][collection].find():
        if MONGO_ID in doc:
            del doc[MONGO_ID]
        ret[doc[key]] = doc
    return ret
