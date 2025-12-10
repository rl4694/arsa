#!/usr/bin/env python3
# /scripts/generate_map.py

import requests
from PIL import Image, ImageDraw
from pathlib import Path

API_URL = "https://arsa.pythonanywhere.com/natural_disasters/"
# These can be changed accordingly
ROOT = Path(__file__).resolve().parent.parent
MAP_FILE = ROOT / "world_map.png"
OUTPUT = ROOT / "natural_disasters_map.png"

# We can expose these later for different type of disasters
DOT_RADIUS = 5
DOT_COLOR = (255, 0, 0, 255)
OUTLINE_COLOR = (0, 0, 0, 200)

def parse_location(loc_value):
    try:
        parts = loc_value.split(",")
        if len(parts) != 2:
            return None
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
        return lat, lon
    except:
        return None

# Convert latitude to longitude to image coordinates
def latlon_to_xy(lat, lon, width, height):
    x = (lon + 180) * (width / 360)
    y = (90 - lat) * (height / 180)
    return int(x), int(y)

def main():
    print("Requesting disaster data from API")
    try:
        resp = requests.get(API_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print("Error: Could not reach API:", e)
        return

    disasters = data.get("disasters", {})
    print(f"Received {len(disasters)} disaster records.")

    print("Loading world_map.png")
    img = Image.open(MAP_FILE).convert("RGBA")
    draw = ImageDraw.Draw(img)
    w, h = img.size # handle different map sizes
    print(f"Map size: {w}x{h}")

    count_plotted = 0

    for _id, d in disasters.items():
        loc = d.get("location")
        if not loc:
            print(f"Skipping {_id}: no location")
            continue

        coords = parse_location(loc)
        if not coords:
            print(f"Skipping {_id}: could not parse location '{loc}'")
            continue

        lat, lon = coords

        # sanity check
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            print(f"Skipping {_id}: invalid lat/lon {coords}")
            continue

        x, y = latlon_to_xy(lat, lon, w, h)

        # Draw a circle with outline
        draw.ellipse(
            (x - DOT_RADIUS, y - DOT_RADIUS, x + DOT_RADIUS, y + DOT_RADIUS),
            fill=DOT_COLOR,
            outline=OUTLINE_COLOR,
            width=2
        )

        print(f"Plotted disaster {_id} at lat={lat} lon={lon} to pixel=({x}, {y})")
        count_plotted += 1

    print(f"Saving output as {OUTPUT}")
    img.save(OUTPUT)

    print(f"Total points plotted: {count_plotted}")

if __name__ == "__main__":
    main()

