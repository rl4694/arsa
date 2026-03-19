import requests
from datetime import datetime

SERVER = "http://127.0.0.1:5000"

RADIUS_KM = 100
DATE_WINDOW_DAYS = 5 # adjust as needed


def date_diff(d1, d2):
    return abs((datetime.fromisoformat(d1) - datetime.fromisoformat(d2)).days)


def get_all_events():
    r = requests.get(f"{SERVER}/natural_disasters")
    return r.json().get("records", [])


def search_nearby(event):
    params = {
        "lat": event["latitude"],
        "lon": event["longitude"],
        "radius_km": RADIUS_KM,
        "date_start": event["date"],
        "date_end": event["date"],
        "type": event["type"]
    }

    r = requests.get(f"{SERVER}/natural_disasters/search", params=params)
    return r.json().get("records", [])


def link(event_id, report_id):
    url = f"{SERVER}/natural_disasters/{event_id}/reports/{report_id}"
    r = requests.post(url)
    print(f"Linked {report_id} → {event_id}")


def main():

    events = get_all_events()

    # Map id → event
    id_map = {e["_id"]: e for e in events}

    for event in events:

        # Skip hidden
        if not event.get("show", True):
            continue

        base_id = event["_id"]

        nearby = search_nearby(event)

        for candidate in nearby:

            cid = candidate["_id"]

            if cid == base_id:
                continue

            # Skip if already hidden
            if not candidate.get("show", True):
                continue

            # Check stricter date window
            if date_diff(event["date"], candidate["date"]) > DATE_WINDOW_DAYS:
                continue

            # Avoid double linking (simple rule: only link higher id → lower id)
            if cid < base_id:
                continue

            link(base_id, cid)


if __name__ == "__main__":
    main()