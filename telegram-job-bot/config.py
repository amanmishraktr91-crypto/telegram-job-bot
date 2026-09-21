import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()

# Tokens & Keys
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "").strip()

# Target Telegram Channel ID or Username (e.g. "@my_new_job_channel" or "-1001234567890")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "").strip()

# Authorized Admin Telegram User IDs (comma-separated, e.g. "123456789,987654321")
# If empty, default user operations are permitted
raw_admins = os.getenv("ADMIN_USER_IDS", "").strip()
ADMIN_USER_IDS = [int(uid.strip()) for uid in raw_admins.split(",") if uid.strip().isdigit()]

# Anti-scam filter threshold
CONFIDENCE_THRESHOLD = 0.75  # Ultra-strict threshold


