import os
from datetime import timedelta


def _csv_env(name, default):
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


class Config:
    DB_USER = os.getenv("DB_USER", "my_user")
    DB_PASS = os.getenv("DB_PASSWORD", "my_password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_NAME = os.getenv("DB_NAME", "my_database")

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:3306/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

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
