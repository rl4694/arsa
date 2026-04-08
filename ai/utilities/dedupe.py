import requests
from datetime import datetime, timedelta
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--server", required=True)
args = parser.parse_args()

SERVER = args.server

DISASTER_RULES = {
    "earthquake": {"radius_km": 25, "date_window_days": 2},
    "landslide":  {"radius_km": 10, "date_window_days": 3},
    "tsunami":    {"radius_km": 150, "date_window_days": 2},
    "hurricane":  {"radius_km": 300, "date_window_days": 7},
}
DEFAULT_RULE = {"radius_km": 10, "date_window_days": 3}
DRY_RUN = False       # set True to preview links without writing


def get_rule(event_type):
    return DISASTER_RULES.get(event_type, DEFAULT_RULE)


def parse_date(date_str):
    return datetime.fromisoformat(date_str)


def date_diff(d1, d2):
    return abs((parse_date(d1) - parse_date(d2)).days)


def get_all_events():
    r = requests.get(f"{SERVER}/natural_disasters")
    r.raise_for_status()
    return r.json().get("records", [])


def get_date_window(date_str, date_window_days):
    base = parse_date(date_str)
    start = (base - timedelta(days=date_window_days)).date().isoformat()
    end = (base + timedelta(days=date_window_days)).date().isoformat()
    return start, end


def search_nearby(event):
    rule = get_rule(event["type"])
    date_start, date_end = get_date_window(event["date"], rule["date_window_days"])

    params = {
        "lat": event["latitude"],
        "lon": event["longitude"],
        "radius_km": rule["radius_km"],
        "date_start": date_start,
        "date_end": date_end,
        "type": event["type"]
    }

    r = requests.get(f"{SERVER}/natural_disasters/search", params=params)
    r.raise_for_status()
    return r.json().get("records", [])


def link(event_id, report_id):
    if DRY_RUN:
        print(f"[DRY RUN] Would link {report_id} → {event_id}")
        return

    url = f"{SERVER}/natural_disasters/{event_id}/reports/{report_id}"
    r = requests.post(url)
    r.raise_for_status()
    print(f"Linked {report_id} → {event_id}")


def choose_root(event, id_map):
    """
    Follow parent chain upward so we always attach to the top-level parent.
    """
    current = event
    seen = set()

    while current.get("parent_event"):
        parent_id = current["parent_event"]

        if parent_id in seen:
            print(f"Warning: detected parent cycle at {parent_id}")
            break
        seen.add(parent_id)

        parent = id_map.get(parent_id)
        if not parent:
            break

        current = parent

    return current


def should_skip_candidate(candidate, root_id):
    """
    Skip candidates that should not be relinked.
    """
    if not candidate.get("show", True):
        return True

    if candidate.get("parent_event"):
        return True

    if candidate["_id"] == root_id:
        return True

    return False


def main():
    events = get_all_events()

    # Map id → event
    id_map = {e["_id"]: e for e in events}

    for event in events:
        # Skip hidden/child events
        if not event.get("show", True):
            continue

        if event.get("parent_event"):
            continue

        root_event = choose_root(event, id_map)
        root_id = root_event["_id"]
        rule = get_rule(root_event["type"])

        nearby = search_nearby(root_event)

        for candidate in nearby:
            cid = candidate["_id"]

            if should_skip_candidate(candidate, root_id):
                continue

            # Extra safety: same type only
            if candidate.get("type") != root_event.get("type"):
                continue

            # Check stricter date window
            if date_diff(root_event["date"], candidate["date"]) > rule["date_window_days"]:
                continue

            # Avoid double linking by only linking "later" ids under "earlier" ids
            # so we do not create A->B and B->A on different passes.
            if cid < root_id:
                continue

            try:
                link(root_id, cid)

                # Update local state so later iterations do not process stale data
                candidate["show"] = False
                candidate["parent_event"] = root_id

                # Keep id_map in sync
                id_map[cid] = candidate

            except requests.RequestException as e:
                print(f"Failed to link {cid} → {root_id}: {e}")


if __name__ == "__main__":
    main()