import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from app.api.router import register_blueprints, register_sockets
from app.config.settings import Config
from app.extensions.db import db, init_db
from app.extensions.socketio import socketio

load_dotenv(override=False)


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
        resources={r"/*": {"origins": "*"}},
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    JWTManager(app)

    register_blueprints(app)

    socketio.init_app(app)
    register_sockets(socketio)

    return app
