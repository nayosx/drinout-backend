from db import db


class GarmentType(db.Model):
    __tablename__ = "garment_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(30), nullable=True)
    is_frequent = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(50), nullable=False, default="CLOTHING")
    active = db.Column(db.Boolean, nullable=False, default=True)
    default_unit_type = db.Column(db.String(20), nullable=False, default="UNIT")
    default_unit_price = db.Column(db.Numeric(10, 2), nullable=True)
    display_order = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f"<GarmentType id={self.id} name={self.name}>"
