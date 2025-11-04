from pymongo import MongoClient


def save_json(filename: str, data: dict):
    raise NotImplementedError("save_json() deprecated after MongoDB migration.")


def load_json(filename: str) -> dict:
    raise NotImplementedError("load_json() deprecated after MongoDB migration.")

def get_db():
    client = MongoClient("mongodb://localhost:27017")
    return client["arsa_db"]


def save_to_mongo(collection: str, data: dict):
    db = get_db()
    col = db[collection]
    col.replace_one({'_id': data['_id']}, data, upsert=True)


def load_from_mongo(collection: str, _id):
    db = get_db()
    col = db[collection]
    return col.find_one({'_id': _id})
