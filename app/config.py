import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_IDS = [x.strip() for x in os.getenv("ADMIN_CHAT_IDS", "").split(",") if x.strip()]


def is_admin(chat_id) -> bool:
    """chat_id boleh int atau str (Telegram ngasihnya int, .env-nya string)."""
    return str(chat_id) in ADMIN_CHAT_IDS

APP_ENV = os.getenv("APP_ENV", "development")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-q4_0")