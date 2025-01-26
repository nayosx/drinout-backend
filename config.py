import os
from datetime import timedelta

class Config:
    DB_USER = os.getenv("DB_USER", "my_user")
    DB_PASS = os.getenv("DB_PASSWORD", "my_password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_NAME = os.getenv("DB_NAME", "my_database")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:3306/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.getenv("SECRET_KEY", "mysuperawesome")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwtawesometoken")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=1)
