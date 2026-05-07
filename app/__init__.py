import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, request
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate

from app.api.router import register_blueprints, register_sockets
from app.extensions.db import db, init_db
from app.extensions.socketio import socketio


def _load_local_env():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)
        return str(env_path)
    return None


def _resolve_cors_origin(origin, allowed_origins):
    if not origin:
        return None
    if "*" in allowed_origins:
        return origin
    if origin in allowed_origins:
        return origin
    return None


def create_app():
    local_env_path = _load_local_env()
    from app.config.settings import Config

    app = Flask(__name__)

    app.config.from_object(Config)

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        print("DB_USER:", os.getenv("DB_USER"))
        print("DB_HOST:", os.getenv("DB_HOST"))
        print("DB_NAME:", os.getenv("DB_NAME"))
        print("LOCAL_ENV_FILE:", local_env_path or "not found")
        print("SQLALCHEMY_DB_HOST:", app.config["DB_HOST"])

    init_db(app)
    Migrate(app, db)

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        allowed_origins = app.config["CORS_ORIGINS"]
        allowed_origin = _resolve_cors_origin(origin, allowed_origins)

        if not allowed_origin:
            return response

        response.headers["Access-Control-Allow-Origin"] = allowed_origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Methods"] = ",".join(app.config["CORS_METHODS"])
        response.headers["Access-Control-Allow-Headers"] = ",".join(app.config["CORS_ALLOW_HEADERS"])
        response.headers["Access-Control-Expose-Headers"] = ",".join(app.config["CORS_EXPOSE_HEADERS"])
        response.headers["Access-Control-Max-Age"] = str(app.config["CORS_MAX_AGE"])

        if app.config["CORS_SUPPORTS_CREDENTIALS"]:
            response.headers["Access-Control-Allow-Credentials"] = "true"

        if request.method == "OPTIONS":
            response.status_code = 200

        return response

    JWTManager(app)

    Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=[app.config.get("RATELIMIT_DEFAULT", "100 per minute")],
        storage_uri=app.config.get("RATELIMIT_STORAGE_URI", "memory://"),
    )

    register_blueprints(app)

    socketio.init_app(app)
    register_sockets(socketio)

    return app
