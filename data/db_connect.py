"""
All interaction with MongoDB should be through this file!
We may be required to use a new database at any point.
"""
import os
from functools import wraps
import pymongo as pm

LOCAL = "0"
CLOUD = "1"
SE_DB = 'seDB'

client = None
MONGO_ID = '_id'


def needs_db(func):
    """
    Decorator that ensures a database connection exists before executing
    a function. Automatically calls connect_db() if the client is not
    already connected.
    
    Usage:
        @needs_db
        def my_function():
            # Access global client here
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        global client
        if not client:
            connect_db()
        return func(*args, **kwargs)
    return wrapper


def connect_db():
    """
    This provides a uniform way to connect to the DB across all uses.
    Returns a mongo client object and also set global client variable.
    
    Connection priority:
    1. Check CLOUD_MONGO environment variable
    2. If CLOUD is set, use cloud MongoDB with credentials
    3. Otherwise, use local MongoDB instance
    
    Raises:
        ValueError: If cloud MongoDB is requested but password not set
    """
    global client
    if client is None:  # not connected yet!
        print('Setting client because it is None.')
        if os.environ.get('CLOUD_MONGO', LOCAL) == CLOUD:
            password = os.environ.get('MONGO_PASSWD')
            if not password:
                raise ValueError('You must set your password '
                                + 'to use Mongo in the cloud.')
            print('Connecting to Mongo in the cloud.')
            client = pm.MongoClient(f'mongodb+srv://gcallah:{password}'
                                    + '@koukoumongo1.yud9b.mongodb.net/'
                                    + '?retryWrites=true&w=majority')
        else:
            print("Connecting to Mongo locally.")
            client = pm.MongoClient()
    return client


def convert_mongo_id(doc: dict):
    """
    Convert MongoDB ObjectId to string for JSON serialization.
    """
    if MONGO_ID in doc:
        doc[MONGO_ID] = str(doc[MONGO_ID])


@needs_db
def create(collection, doc, db=SE_DB):
    """
    Insert a single doc into collection.
    
    Args:
        collection: Collection name
        doc: Document to insert
        db: Database name (default: SE_DB)
    
    Returns:
        InsertResult with inserted_id
    """
    print(f'{db=}')
    return client[db][collection].insert_one(doc)


@needs_db
def read_one(collection, filt, db=SE_DB):
    """
    Find with a filter and return the first doc found.
    Converts MongoDB ID to string.
    
    Args:
        collection: Collection name
        filt: Filter dictionary
        db: Database name (default: SE_DB)
    
    Returns:
        First matching document or None if not found
    """
    for doc in client[db][collection].find(filt):
        convert_mongo_id(doc)
        return doc
    return None


@needs_db
def delete(collection: str, filt: dict, db=SE_DB):
    """
    Delete document(s) matching filter from collection.
    
    Args:
        collection: Collection name
        filt: Filter dictionary
        db: Database name (default: SE_DB)
    
    Returns:
        Number of documents deleted
    """
    print(f'{filt=}')
    del_result = client[db][collection].delete_one(filt)
    return del_result.deleted_count


@needs_db
def update(collection, filters, update_dict, db=SE_DB):
    """
    Update document(s) in collection matching filters.
    
    Args:
        collection: Collection name
        filters: Filter dictionary to match documents
        update_dict: Dictionary of fields to update
        db: Database name (default: SE_DB)
    
    Returns:
        UpdateResult
    """
    return client[db][collection].update_one(filters, {'$set': update_dict})


@needs_db
def read(collection, db=SE_DB, no_id=True) -> list:
    """
    Returns a list of all documents from the collection.
    
    Args:
        collection: Collection name
        db: Database name (default: SE_DB)
        no_id: If True, removes _id field from documents (default: True)
    
    Returns:
        List of documents
    """
    ret = []
    for doc in client[db][collection].find():
        if no_id:
            del doc[MONGO_ID]
        else:
            convert_mongo_id(doc)
        ret.append(doc)
    return ret


@needs_db
def read_dict(collection, key, db=SE_DB, no_id=True) -> dict:
    """
    Returns documents as a dictionary keyed by specified field.
    
    Args:
        collection: Collection name
        key: Field to use as dictionary key
        db: Database name (default: SE_DB)
        no_id: If True, removes _id field from documents (default: True)
    
    Returns:
        Dictionary with specified key as keys and documents as values
    """
    recs = read(collection, db=db, no_id=no_id)
    recs_as_dict = {}
    for rec in recs:
        recs_as_dict[rec[key]] = rec
    return recs_as_dict


@needs_db
def fetch_all_as_dict(key, collection, db=SE_DB):
    """
    Fetch all documents and return as dictionary keyed by specified field.
    
    Args:
        key: Field to use as dictionary key
        collection: Collection name
        db: Database name (default: SE_DB)
    
    Returns:
        Dictionary with specified key as keys and documents as values
    """
    ret = {}
    for doc in client[db][collection].find():
        del doc[MONGO_ID]
        ret[doc[key]] = doc
    return ret
