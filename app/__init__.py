import os

from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

load_dotenv(override=False)

from app.api.router import register_blueprints, register_sockets
from app.config.settings import Config
from app.extensions.db import db, init_db
from app.extensions.socketio import socketio


def _resolve_cors_origin(origin, allowed_origins):
    if not origin:
        return None
    if "*" in allowed_origins:
        return origin
    if origin in allowed_origins:
        return origin
    return None


def create_app():
    app = Flask(__name__)

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        print("DB_USER:", os.getenv("DB_USER"))
        print("DB_HOST:", os.getenv("DB_HOST"))
        print("DB_NAME:", os.getenv("DB_NAME"))
        print("ENV FILE LOADED")

    app.config.from_object(Config)

    init_db(app)
    Migrate(app, db)

    CORS(
        app,
        resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}},
        allow_headers=app.config["CORS_ALLOW_HEADERS"],
        expose_headers=app.config["CORS_EXPOSE_HEADERS"],
        methods=app.config["CORS_METHODS"],
        supports_credentials=app.config["CORS_SUPPORTS_CREDENTIALS"],
        max_age=app.config["CORS_MAX_AGE"],
        vary_header=True,
    )

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        allowed_origin = _resolve_cors_origin(origin, app.config["CORS_ORIGINS"])
        if not allowed_origin:
            return response

        response.headers.setdefault("Access-Control-Allow-Origin", allowed_origin)
        response.headers.setdefault("Vary", "Origin")
        response.headers.setdefault("Access-Control-Allow-Methods", ",".join(app.config["CORS_METHODS"]))
        response.headers.setdefault("Access-Control-Allow-Headers", ",".join(app.config["CORS_ALLOW_HEADERS"]))
        response.headers.setdefault("Access-Control-Expose-Headers", ",".join(app.config["CORS_EXPOSE_HEADERS"]))
        response.headers.setdefault("Access-Control-Max-Age", str(app.config["CORS_MAX_AGE"]))

        if app.config["CORS_SUPPORTS_CREDENTIALS"]:
            response.headers.setdefault("Access-Control-Allow-Credentials", "true")

        return response

    JWTManager(app)

    register_blueprints(app)

    socketio.init_app(app)
    register_sockets(socketio)

    return app
