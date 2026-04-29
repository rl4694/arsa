import argparse
import os
import requests
import sys
from datetime import date
from google import genai
from google.genai import types
from google.genai import errors

# Comprehensive 2026 Model Priority List
FULL_MODEL_LIST = [
    "gemini-2.5-flash",             # Stable Price/Performance (This is the only one that works so far)
    "gemini-2.5-flash-lite",        # Massive volume/Low latency
]

# Bookmark system for rate limiting
RUN_BOOKMARK = "ai/last_successful_run.txt"

def already_ran_today(target_date):
    if not os.path.exists(RUN_BOOKMARK):
        return False

    with open(RUN_BOOKMARK, "r") as f:
        last_run = f.read().strip()

    return last_run == target_date

def record_successful_run(target_date):
    with open(RUN_BOOKMARK, "w") as f:
        f.write(target_date)

def results_exist_for_date(server, target_date):
    """
    Query the disasters API to see if entries already exist for the date.
    """
    try:
        url = f"{server.rstrip('/')}/natural_disasters?date={target_date}"
        r = requests.get(url, timeout=10)

        if r.status_code != 200:
            return False

        data = r.json()
        records = data.get("records", [])

        return len(records) > 0

    except Exception:
        return False

def fetch_disasters(api_key, target_date, country, server):

    api_key = api_key.strip(' "\'\n\r')
    if not api_key:
        print("Error: API key is empty.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    location_context = f"in {country}" if country else "worldwide"
    server = server.rstrip("/") # small input fix

    # Filter list if user requested only high-end 'Pro' models
    priority_list = FULL_MODEL_LIST

    prompt = f"""
Find significant natural disasters reported on {target_date} {location_context}.

Include all major natural disaster types when reported, including but not limited to:
earthquake, hurricane, landslide, tsunami, wildfire, flood, tornado, volcano,
winter storm, drought, heat wave, avalanche, cyclone, typhoon, severe storm,
mudslide, sinkhole, blizzard, hailstorm, and dust storm.

Use lowercase type names.

Set "severity" as follows:
- earthquake: earthquake magnitude
- hurricane, cyclone, typhoon: storm category number when available
- tornado: EF rating number when available
- wildfire, flood, landslide, tsunami, volcano, winter storm, drought, heat wave,
  avalanche, severe storm, mudslide, sinkhole, blizzard, hailstorm, dust storm:
  use a 1-5 severity scale based on reported damage, deaths, evacuations, area affected,
  intensity, and disruption
- if severity cannot be reasonably estimated, use null

Output ONLY curl commands with no explanation.
Each command must follow this format exactly:
curl -X POST {server}/natural_disasters/ \\
-H "X-Auth-Bypass-Key: $AUTH_BYPASS_KEY" \\
-H "Content-Type: application/json" \\
-d '{{
"name": "[event name]",
"type": "[lowercase disaster type]",
"date": "{target_date}",
"latitude": [decimal],
"longitude": [decimal],
"description": "[short description]",
"severity": [number or null]
}}'
"""

    # Stage 1: Search-enabled Loop (requires specific quota)
    # Stage 2: No-Search Loop (fallback to internal knowledge)
    # for use_search in [True, False]: (disabling no search for now)
    for use_search in [True]:
        mode = "WITH SEARCH" if use_search else "INTERNAL KNOWLEDGE (NO SEARCH)"
        print(f"\n--- Strategy: {mode} ---", file=sys.stderr)

        for model_name in priority_list:
            print(f"Trying {model_name}...", file=sys.stderr, end=" ")
            
            config_kwargs = {}
            if use_search:
                config_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]

            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(**config_kwargs) if config_kwargs else None
                )
                
                if response.text:
                    print("SUCCESS!", file=sys.stderr)
                    print(response.text)
                    record_successful_run(target_date)
                    return

            except errors.APIError as e:
                # Catches 429 (Quota), 503 (Unavailable), and 403 (Permission)
                msg = str(e).split('.')[0]
                print(f"FAILED ({msg})", file=sys.stderr)
                continue 

    print("\n[!] Error: All models and strategies failed.", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--country", default=None)
    # New Optional Field: Forces the script to only use Pro-tier models
    # This doesn't seem to work right now, so it might be replaced
    # parser.add_argument("--pro-only", action="store_true", help="Skip Flash/Lite models and only use high-end Pro models")
    parser.add_argument(
        "--server",
        default="http://127.0.0.1:8000",
        help="Server base URL for the natural disasters API"
    )

    args = parser.parse_args()

    # Check Bookmark First
    if already_ran_today(args.date):
        print(f"Script already ran successfully for {args.date}. Skipping.", file=sys.stderr)
        sys.exit(0)

    # Check API
    if results_exist_for_date(args.server, args.date):
        print(f"Disasters already exist for {args.date}. Skipping generation.", file=sys.stderr)
        sys.exit(0)

    fetch_disasters(args.key, args.date, args.country, args.server)