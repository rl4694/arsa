import requests
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--server", required=True)
parser.add_argument("--token", default=None)
args = parser.parse_args()

SERVER = args.server.rstrip("/")
HEADERS = {"Authorization": f"Bearer {args.token}"} if args.token else {}


def get_all_records():
    r = requests.get(f"{SERVER}/natural_disasters", headers=HEADERS)
    r.raise_for_status()
    data = r.json()
    records = data.get("records", [])

    if isinstance(records, dict):
        return list(records.values())

    if isinstance(records, list):
        return records

    raise TypeError(f"Expected records to be a list or dict, got {type(records).__name__}")


def main():
    records = get_all_records()

    for record in records:
        _id = record["_id"]
        update = {}

        if "show" not in record:
            update["show"] = True

        if "reports" not in record:
            update["reports"] = []

        if "parent_event" not in record:
            update["parent_event"] = None

        if "severity" not in record:
            update["severity"] = None

        if update:
            resp = requests.put(
                f"{SERVER}/natural_disasters/{_id}",
                json=update,
                headers=HEADERS
            )
            resp.raise_for_status()
            print(f"Backfilled {_id}")


if __name__ == "__main__":
    main()