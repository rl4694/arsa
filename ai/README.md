## disaster_scraper.py – Parameters

--key        (required)  Gemini API key used to fetch disaster data.
--date       (optional)  Date to query disasters for (YYYY-MM-DD). Defaults to today.
--country    (optional)  Filter disasters by country name.
--server     (optional)  Base URL of the natural disasters API where generated `curl` commands will be sent. Defaults to `http://127.0.0.1:8000`.

The script will only run **once per date**. After a successful run, it records the date in `ai/last_successful_run.txt`. If the script is executed again with the same date, it will exit without running.

Example:

python ai/disaster_scraper.py --key YOUR_API_KEY
python ai/disaster_scraper.py --key YOUR_API_KEY --date 2026-03-10
python ai/disaster_scraper.py --key YOUR_API_KEY --country Japan
python ai/disaster_scraper.py --key YOUR_API_KEY --server [http://localhost:8000](http://localhost:8000)
python ai/disaster_scraper.py --key YOUR_API_KEY --date 2026-03-10 --country Japan --server [http://localhost:8000](http://localhost:8000)
