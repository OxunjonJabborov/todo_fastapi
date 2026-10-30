import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL muhit o'zgaruvchisi aniqlanmadi...")
DB_ECHO = os.getenv("DB_ECHO", "false").lower() == "true"

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "dev-secret-key-change-me-before-production-32-bytes-minimum",
)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")

FROM_EMAIL = os.getenv("FROM_EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "465"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
