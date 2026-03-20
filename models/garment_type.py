from db import db


class GarmentType(db.Model):
    __tablename__ = "garment_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(30), nullable=True)
    is_frequent = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<GarmentType id={self.id} name={self.name}>"
