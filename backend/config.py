import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "session_booking"),
    "port": int(os.getenv("DB_PORT", 3306))
}

JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "change-this-secret-in-production"
)