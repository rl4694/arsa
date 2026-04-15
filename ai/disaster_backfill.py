import argparse
import json
import math
import os
import requests
import sys
from google import genai
from google.genai import types
from google.genai import errors

FULL_MODEL_LIST = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]


def is_missing_severity(record):
    value = record.get("severity")

    if value is None:
        return True

    if isinstance(value, str):
        if value.strip() == "":
            return True
        try:
            value = float(value)
        except ValueError:
            return True

    if isinstance(value, (int, float)):
        return not math.isfinite(value)

    return True


def has_bad_description(record):
    value = record.get("description")

    if value is None:
        return False

    if not isinstance(value, str):
        return False

    normalized = value.strip().lower()
    return normalized in {
        "trigger: n/a",
        "trigger:n/a",
        "n/a",
        "na",
    }


def needs_repair(record):
    return is_missing_severity(record) or has_bad_description(record)


def get_bypass_headers():
    auth_bypass_key = os.environ.get("AUTH_BYPASS_KEY", "").strip()
    headers = {}

    if auth_bypass_key:
        headers["X-Auth-Bypass-Key"] = auth_bypass_key

    return headers


def fetch_all_disasters(server):
    url = f"{server.rstrip('/')}/natural_disasters"
    headers = get_bypass_headers()

    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()

    data = r.json()
    records = data.get("records", [])

    if isinstance(records, dict):
        return list(records.values())
    if isinstance(records, list):
        return records
    return []


def chunk_records(records, chunk_size):
    for i in range(0, len(records), chunk_size):
        yield records[i:i + chunk_size]


def build_prompt(records, server):
    records_json = json.dumps(records, indent=2, ensure_ascii=False)

    return f"""
You are updating existing natural disaster records to fill in missing severity values and repair bad descriptions.

For each record:
- earthquake => severity = earthquake magnitude if it can be reliably determined, otherwise null
- hurricane => severity = hurricane category number if it can be reliably determined, otherwise null
- landslide => severity = null
- tsunami => severity = null
- any other disaster type => severity = null

Description repair rules:
- If description is exactly "Trigger: N/A" or another obvious placeholder like "N/A" or "NA", replace it.
- Write a short, factual, plain description of the event.
- Prefer using only information already present in the record.
- Do not invent extra details that are not reasonably inferable.
- If little is known, use a safe generic description based on name, type, and date.
- If the existing description is already meaningful, preserve it exactly.

Critical output rules:
- Output ONLY raw curl commands.
- Do NOT output JSON arrays.
- Do NOT output markdown code fences.
- Do NOT output explanations.
- Do NOT output headings.
- Do NOT repeat the input records.
- Start the very first output line with: curl -X PUT
- Every record must produce exactly one curl command.
- Preserve all existing fields exactly as they already are.
- Only change the "severity" field if needed and the "description" field if it is a bad placeholder.
- Keep the same _id already present in each record.
- Use full JSON objects in the -d body.
- Output valid JSON inside each -d body.

Records to update:
{records_json}

Every command must match this exact shape:
curl -X PUT {server.rstrip('/')}/natural_disasters/RECORD_ID \\
-H "X-Auth-Bypass-Key: $AUTH_BYPASS_KEY" \\
-H "Content-Type: application/json" \\
-d '{{ ... full JSON object with updated fields ... }}'
""".strip()


def extract_curl_commands(text):
    if not text:
        return ""

    text = text.replace("```bash", "")
    text = text.replace("```json", "")
    text = text.replace("```sh", "")
    text = text.replace("```shell", "")
    text = text.replace("```", "")

    lines = text.splitlines()
    commands = []
    current = []
    in_command = False

    for line in lines:
        raw_line = line.rstrip("\n")
        stripped = raw_line.strip()

        if stripped.startswith("curl -X PUT "):
            if current:
                commands.append("\n".join(current).strip())
                current = []
            current.append(stripped)
            in_command = True
            continue

        if not in_command:
            continue

        if (
            stripped.startswith("-H ")
            or stripped.startswith("-d ")
            or stripped.startswith("\\")
            or raw_line.startswith("  ")
            or raw_line.startswith("    ")
            or stripped.startswith("{")
            or stripped.startswith("}")
            or stripped.startswith('"')
            or stripped.startswith("'")
            or stripped.startswith("],")
            or stripped.startswith("[")
            or stripped.startswith("]")
            or stripped.startswith("},")
            or stripped.startswith("',")
            or stripped == ""
        ):
            current.append(raw_line)
            if stripped == "":
                commands.append("\n".join(current).strip())
                current = []
                in_command = False
            continue

        if current:
            commands.append("\n".join(current).strip())
            current = []
        in_command = False

    if current:
        commands.append("\n".join(current).strip())

    cleaned = []
    for cmd in commands:
        cmd = cmd.strip()
        if cmd.startswith("curl -X PUT "):
            cleaned.append(cmd)

    return "\n\n".join(cleaned)


def generate_batch_curls(client, prompt):
    for use_search in [True, False]:
        mode = "WITH SEARCH" if use_search else "INTERNAL KNOWLEDGE (NO SEARCH)"
        print(f"\n--- Strategy: {mode} ---", file=sys.stderr)

        for model_name in FULL_MODEL_LIST:
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

                text = (response.text or "").strip()
                if not text:
                    print("FAILED (empty response)", file=sys.stderr)
                    continue

                cleaned = extract_curl_commands(text)
                if cleaned:
                    print("SUCCESS!", file=sys.stderr)
                    return cleaned

                print("FAILED (no curl commands found)", file=sys.stderr)

            except errors.APIError as e:
                msg = str(e).split('.')[0]
                print(f"FAILED ({msg})", file=sys.stderr)
                continue

    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    parser.add_argument(
        "--server",
        default="http://127.0.0.1:8000",
        help="Server base URL for the natural disasters API"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=25,
        help="How many records to send to the AI in one batch"
    )

    args = parser.parse_args()

    api_key = args.key.strip(' "\'\n\r')
    if not api_key:
        print("Error: API key is empty.", file=sys.stderr)
        sys.exit(1)

    if args.chunk_size <= 0:
        print("Error: --chunk-size must be greater than 0.", file=sys.stderr)
        sys.exit(1)

    if not os.environ.get("AUTH_BYPASS_KEY", "").strip():
        print("Error: AUTH_BYPASS_KEY is not set.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    try:
        disasters = fetch_all_disasters(args.server)
    except Exception as e:
        print(f"Error fetching disasters: {e}", file=sys.stderr)
        sys.exit(1)

    missing = [d for d in disasters if needs_repair(d)]

    if not missing:
        print("No disasters with missing severity or bad placeholder descriptions found.", file=sys.stderr)
        sys.exit(0)

    print(f"Found {len(missing)} disasters needing severity/description repair.", file=sys.stderr)

    batch_count = 0
    emitted_batches = 0

    for batch in chunk_records(missing, args.chunk_size):
        batch_count += 1
        print(f"\nProcessing batch {batch_count} with {len(batch)} record(s)...", file=sys.stderr)

        prompt = build_prompt(batch, args.server)
        curl_block = generate_batch_curls(client, prompt)

        if curl_block:
            print(curl_block)
            emitted_batches += 1
        else:
            print(f"Failed to generate curls for batch {batch_count}.", file=sys.stderr)

    print(
        f"\nDone. Processed {len(missing)} record(s) across {batch_count} batch(es). "
        f"Emitted curl blocks for {emitted_batches} batch(es).",
        file=sys.stderr
    )


if __name__ == "__main__":
    main()