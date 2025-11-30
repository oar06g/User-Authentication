import os
from dotenv import load_dotenv

load_dotenv()

# --- Database config ---
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DB_USER_AUTHDB = os.getenv("MYSQL_DB_USER_AUTHDB")
DB_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB_USER_AUTHDB}"

# DB_URL = 'sqlite:///db_user_auth.db'


# --- Send email config ---
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


# --- JWT config ---
SECRET_KEY_JWT = os.getenv("SECRET_KEY_JWT", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 2  # 2 hours


# --- Security config ---
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGITS = True
PASSWORD_REQUIRE_SPECIAL = True

# --- Rate limiting config ---
RATE_LIMIT_PER_MINUTE = 60
RATE_LIMIT_PER_HOUR = 300

# --- Cookie config ---
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "False").lower() == "true"
COOKIE_SAMESITE = "lax"  # 'strict', 'lax', or 'none'
COOKIE_HTTPONLY = True

# --- Application config ---
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # production, development
DEBUG = ENVIRONMENT == "development"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

