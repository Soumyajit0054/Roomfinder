import os
import secrets
import warnings

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# =========================================================
# PROJECT BASE DIRECTORY
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# =========================================================
# MYSQL CONFIGURATION
# =========================================================

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "roomfinder")
}


# =========================================================
# FLASK SECRET KEY
# =========================================================

SECRET_KEY = os.environ.get("SECRET_KEY")

if not SECRET_KEY:
    # No hardcoded fallback: an unset key gets a random one, which logs
    # everyone out on restart and differs between worker processes.
    SECRET_KEY = secrets.token_hex(32)
    warnings.warn(
        "SECRET_KEY is not set; using a random key for this process. "
        "Set SECRET_KEY in the environment or .env for a stable one."
    )


# =========================================================
# UPLOAD DIRECTORY
# =========================================================

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or os.path.join(
    BASE_DIR,
    "static",
    "uploads"
)

# Public base URL used to build absolute image URLs for the API,
# e.g. "https://cdn.example.com/uploads". Empty = serve from this app.
UPLOAD_BASE_URL = os.environ.get("UPLOAD_BASE_URL", "").rstrip("/")

# Lifetime of mobile API tokens, in seconds (default 30 days)
API_TOKEN_MAX_AGE = int(os.environ.get("API_TOKEN_MAX_AGE", 60 * 60 * 24 * 30))


# =========================================================
# ALLOWED IMAGE TYPES
# =========================================================

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "gif",
    "webp",
    "bmp",
    "tif",
    "tiff",
    "svg",
    "ico",
    "avif",
    "heic",
    "heif"
}