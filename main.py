from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy.sql import text
from config import Config
from db import db
from resources.user_resource import user_bp
from resources.auth_resource import auth_bp
from resources.transaction_resource import transaction_bp
from resources.payment_type_resource import payment_type_bp
from resources.work_session_resource import work_session_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    Migrate(app, db)
    
    CORS(app)
    jwt = JWTManager(app)

    with app.app_context():
        with db.engine.connect() as conn:
            conn.execute(text("SET time_zone = '-6:00'"))
            conn.commit()

    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(payment_type_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(work_session_bp)

    @app.before_first_request
    def create_tables():
        db.create_all()

    return app

if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True, host="0.0.0.0", port=5000)
