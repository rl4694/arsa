## disaster_scraper.py – Parameters

--key        (required)  Gemini API key used to fetch disaster data.
--date       (optional)  Date to query disasters for (YYYY-MM-DD). Defaults to today.
--country    (optional)  Filter disasters by country name.

Example:

python ai/disaster_scraper.py --key YOUR_API_KEY
python ai/disaster_scraper.py --key YOUR_API_KEY --date 2026-03-10
python ai/disaster_scraper.py --key YOUR_API_KEY --country Japan