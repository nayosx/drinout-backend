from db import db


class Extra(db.Model):
    __tablename__ = "extras"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    default_price = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, nullable=True, default=True)

    def __repr__(self):
        return f"<Extra id={self.id} name={self.name}>"
