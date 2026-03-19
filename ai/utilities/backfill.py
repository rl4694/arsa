import requests

SERVER = "http://127.0.0.1:5000"

r = requests.get(f"{SERVER}/natural_disasters")
records = r.json()["records"]

for r in records:
    _id = r["_id"]

    update = {}

    if "show" not in r:
        update["show"] = True

    if "reports" not in r:
        update["reports"] = []

    if "parent_event" not in r:
        update["parent_event"] = None

    if "severity" not in r:
        update["severity"] = None

    if update:
        requests.put(f"{SERVER}/natural_disasters/{_id}", json=update)
        print(f"Backfilled {_id}")