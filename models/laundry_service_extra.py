from db import db


class LaundryServiceExtra(db.Model):
    __tablename__ = "laundry_service_extras"

    id = db.Column(db.Integer, primary_key=True)
    laundry_service_id = db.Column(
        db.Integer,
        db.ForeignKey("laundry_services.id"),
        nullable=False,
    )
    extra_id = db.Column(
        db.Integer,
        db.ForeignKey("extras.id"),
        nullable=False,
    )
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    is_courtesy = db.Column(db.Boolean, nullable=True, default=False)

    laundry_service = db.relationship("LaundryService")
    extra = db.relationship("Extra")

    def __repr__(self):
        return f"<LaundryServiceExtra id={self.id} laundry_service_id={self.laundry_service_id}>"
