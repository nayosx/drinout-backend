from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

db = SQLAlchemy()

def _set_time_zone(conn, _):
    cur = conn.cursor()
    cur.execute("SET time_zone = '+00:00'")
    cur.close()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        event.listen(db.engine, "connect", _set_time_zone)
