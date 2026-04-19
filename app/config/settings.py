import os
from datetime import timedelta


def _csv_env(name, default):
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _require_env(name):
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


class Config:
    DB_USER = _require_env("DB_USER")
    DB_PASS = _require_env("DB_PASSWORD")
    DB_HOST = _require_env("DB_HOST")
    DB_NAME = _require_env("DB_NAME")

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:3306/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": os.getenv("DB_POOL_PRE_PING", "true").lower() in ("true", "1", "t", "yes"),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "1800")),
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
    }

    SECRET_KEY = os.getenv("SECRET_KEY", "mysuperawesome")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwtawesometoken")

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=9)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=1)

    CORS_ORIGINS = _csv_env("CORS_ORIGINS", "*")
    CORS_ALLOW_HEADERS = _csv_env(
        "CORS_ALLOW_HEADERS",
        "Authorization,Content-Type,Accept,Origin,X-Requested-With,Cache-Control,Pragma",
    )
    CORS_EXPOSE_HEADERS = _csv_env(
        "CORS_EXPOSE_HEADERS",
        "Authorization,Content-Type",
    )
    CORS_METHODS = _csv_env(
        "CORS_METHODS",
        "GET,POST,PUT,PATCH,DELETE,OPTIONS",
    )
    CORS_SUPPORTS_CREDENTIALS = os.getenv("CORS_SUPPORTS_CREDENTIALS", "false").lower() in (
        "true",
        "1",
        "t",
        "yes",
    )
    CORS_MAX_AGE = int(os.getenv("CORS_MAX_AGE", "86400"))
