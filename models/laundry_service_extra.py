from db import db


class LaundryServiceExtra(db.Model):
    __tablename__ = "laundry_service_extras"

    id = db.Column(db.Integer, primary_key=True)
    laundry_service_id = db.Column(
        db.Integer,
        db.ForeignKey("laundry_services.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    service_extra_type_id = db.Column(
        db.Integer,
        db.ForeignKey("service_extra_types.id", onupdate="CASCADE"),
        nullable=False,
    )
    quantity = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=True)
    subtotal = db.Column(db.Numeric(10, 2), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    laundry_service = db.relationship("LaundryService", back_populates="extras")
    service_extra_type = db.relationship("ServiceExtraType", back_populates="service_extras")

    def __repr__(self):
        return f"<LaundryServiceExtra id={self.id} service={self.laundry_service_id}>"
