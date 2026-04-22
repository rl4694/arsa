from dotenv import load_dotenv
import os

is_env_loaded = False


def get_env(key: str, default=None):
    global is_env_loaded
    if not is_env_loaded:
        load_dotenv()
        is_env_loaded = True
    return os.environ.get(key, default)
