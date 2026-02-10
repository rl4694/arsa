import json
import time
from pathlib import Path

from server.etl.geocoding import forward_geocode

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "server" / "etl" / "cities.json"
OUTPUT_PATH = BASE_DIR / "server" / "etl" / "cities_with_coords.json"

MAX_COUNT = 50

def main():
    if OUTPUT_PATH.exists():
        with OUTPUT_PATH.open() as f:
            cities = json.load(f)
    else:
        with INPUT_PATH.open() as f:
            cities = json.load(f)
    processed = 0
    for _id, record in cities.items():
        if "latitude" in record and "longitude" in record:
            continue
        if processed >= MAX_COUNT:
            break

        name = record["name"]
        state = record["state_name"]
        nation = record["nation_name"]
        query = f"{name}, {state}, {nation}"

        print("Geocoding:", query)
        lat, lon = forward_geocode(query)
        if lat is not None:
            record["latitude"] = lat
            record["longitude"] = lon
        else:
            print("  -> no result, leaving without coords")

        processed += 1
        time.sleep(1)  # respect Nominatim rate limits

    with OUTPUT_PATH.open("w") as f:
        json.dump(cities, f, ensure_ascii=True, indent=2)

    print(f"Processed {processed} cities this run")

if __name__ == "__main__":
    main()
