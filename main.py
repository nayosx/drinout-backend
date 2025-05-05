import os
from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from db import db, init_db
from resources.user_resource import user_bp
from resources.auth_resource import auth_bp
from resources.transaction_resource import transaction_bp
from resources.payment_type_resource import payment_type_bp
from resources.work_session_resource import work_session_bp
from resources.test_resource import test_bp
from resources.task_resource import task_bp
from resources.menu_resource import menu_bp
from resources.role_resource import role_bp

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)
    Migrate(app, db)
    CORS(app)
    JWTManager(app)
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(payment_type_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(work_session_bp)
    app.register_blueprint(test_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(role_bp)

    @app.before_first_request
    def create_tables():
        db.create_all()

    return app

if __name__ == "__main__":
    flask_app = create_app()
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    flask_app.run(debug=debug, host="0.0.0.0", port=port)
