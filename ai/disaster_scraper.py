import argparse
import sys
from datetime import date
from google import genai
from google.genai import types
from google.genai import errors

# Comprehensive 2026 Model Priority List
FULL_MODEL_LIST = [
    "gemini-3.1-pro-preview",       # Top tier: Latest SOTA reasoning
    "gemini-3-pro",                 # High end: Advanced multimodal
    "gemini-3-flash",               # High speed: Frontier performance
    "gemini-2.5-pro",               # Stable High-end GA
    "gemini-3.1-flash-lite-preview",# Newest scale-optimized (Mar 2026)
    "gemini-2.5-flash",             # Stable Price/Performance (This is the only one that works so far)
    "gemini-2.5-flash-lite",        # Massive volume/Low latency
]

def fetch_disasters(api_key, target_date, country, pro_only=False):
    client = genai.Client(api_key=api_key)
    location_context = f"in {country}" if country else "worldwide"

    # Filter list if user requested only high-end 'Pro' models
    priority_list = [m for m in FULL_MODEL_LIST if "pro" in m] if pro_only else FULL_MODEL_LIST

    prompt = f"""
Find significant natural disasters reported on {target_date} {location_context}.
Include earthquakes, hurricanes, floods, landslides, or tsunamis.

Output ONLY curl commands with no explanation.
Each command must follow this format exactly:
curl -X POST http://127.0.0.1:5000/natural_disasters/ \\
-H "Content-Type: application/json" \\
-d '{{
"name": "[event name]",
"type": "[earthquake|landslide|tsunami|hurricane]",
"date": "{target_date}",
"latitude": [decimal],
"longitude": [decimal],
"description": "[short description]"
}}'
"""

    # Stage 1: Search-enabled Loop (requires specific quota)
    # Stage 2: No-Search Loop (fallback to internal knowledge)
    for use_search in [True, False]:
        mode = "WITH SEARCH" if use_search else "INTERNAL KNOWLEDGE (NO SEARCH)"
        print(f"\n--- Strategy: {mode} ---", file=sys.stderr)

        for model_name in priority_list:
            print(f"Trying {model_name}...", file=sys.stderr, end=" ")
            
            config = {"temperature": 0.0}
            if use_search:
                config["tools"] = [types.Tool(google_search=types.GoogleSearch())]

            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(**config)
                )
                
                if response.text:
                    print("SUCCESS!", file=sys.stderr)
                    print(response.text)
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
    parser.add_argument("--pro-only", action="store_true", help="Skip Flash/Lite models and only use high-end Pro models")

    args = parser.parse_args()
    fetch_disasters(args.key, args.date, args.country, args.pro_only)