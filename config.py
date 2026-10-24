import os
from pathlib import Path

# Automatically load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Base configuration settings for HouseRent."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "houserent-dev-secret-key-2026-bca-microproject")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "database" / "houserent.db"))
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", str(BASE_DIR / "static" / "uploads"))
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB maximum upload size
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() in ("true", "1", "yes")
    TESTING = False
    PORT = int(os.environ.get("PORT", 5000))

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration with an isolated in-memory or temporary database."""
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test-secret-key-isolated-env"
    DATABASE_PATH = ":memory:"
    UPLOAD_FOLDER = str(BASE_DIR / "static" / "uploads")

class ProductionConfig(Config):
    """Production configuration suitable for containerized, VM, and cloud deployments (e.g., Render)."""
    DEBUG = False
    SESSION_COOKIE_SECURE = os.environ.get(
        "SESSION_COOKIE_SECURE",
        "true" if os.environ.get("RENDER") else "false"
    ).lower() in ("true", "1", "yes")
    SECRET_KEY = os.environ.get("SECRET_KEY") or "houserent-prod-secure-env-fallback-key"

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

