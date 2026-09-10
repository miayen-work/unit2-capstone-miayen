import os

from dotenv import load_dotenv

load_dotenv()

# The embedding model is downloaded once by scripts/setup_data.py; forcing offline
# mode afterward avoids a network call to the HF Hub on every query, which can hang
# indefinitely with no timeout instead of failing fast.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
