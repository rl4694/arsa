# ai/utilities/snapshot_natural_disasters.py

import json
import os
from datetime import datetime
from data.db_connect import CRUD

COLLECTION = "natural_disasters"
SNAPSHOT_DIR = "db_snapshots/natural_disasters"


def main():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    crud = CRUD(COLLECTION)
    records = crud.read()

    latest_path = os.path.join(SNAPSHOT_DIR, "latest.json")

    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    archive_path = os.path.join(SNAPSHOT_DIR, f"{timestamp}.json")

    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"Saved latest snapshot: {latest_path}")
    print(f"Saved archive snapshot: {archive_path}")


if __name__ == "__main__":
    main()