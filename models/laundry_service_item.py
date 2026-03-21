from db import db


class LaundryServiceItem(db.Model):
    __tablename__ = "laundry_service_items"

    id = db.Column(db.Integer, primary_key=True)
    laundry_service_id = db.Column(
        db.Integer,
        db.ForeignKey("laundry_services.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    garment_type_id = db.Column(
        db.Integer,
        db.ForeignKey("garment_types.id", onupdate="CASCADE"),
        nullable=False,
    )
    quantity = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    unit_type = db.Column(db.String(20), nullable=False, default="UNIT")
    unit_price = db.Column(db.Numeric(10, 2), nullable=True)
    subtotal = db.Column(db.Numeric(10, 2), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    laundry_service = db.relationship("LaundryService", back_populates="items")
    garment_type = db.relationship("GarmentType", back_populates="service_items")

    def __repr__(self):
        return f"<LaundryServiceItem id={self.id} service={self.laundry_service_id}>"
