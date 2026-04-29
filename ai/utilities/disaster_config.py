# ai/utilities/disaster_config.py

DISASTER_TYPES = {
    "earthquake": {"radius_km": 100, "date_window_days": 2},
    "landslide": {"radius_km": 100, "date_window_days": 3},
    "tsunami": {"radius_km": 150, "date_window_days": 2},
    "hurricane": {"radius_km": 300, "date_window_days": 7},
}

DEFAULT_DEDUPE = {"radius_km": 10, "date_window_days": 3}