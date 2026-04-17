from db import db


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    laundry_service_id = db.Column(
        db.Integer,
        db.ForeignKey("laundry_services.id"),
        nullable=False,
    )
    service_id = db.Column(
        db.Integer,
        db.ForeignKey("services.id"),
        nullable=False,
    )
    service_variant_id = db.Column(
        db.Integer,
        db.ForeignKey("service_variants.id"),
        nullable=True,
    )
    garment_type_id = db.Column(
        db.Integer,
        db.ForeignKey("garment_types.id"),
        nullable=True,
    )
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_catalog_price = db.Column(db.Numeric(10, 2), nullable=True)
    catalog_price = db.Column(db.Numeric(10, 2), nullable=False)
    applied_price = db.Column(db.Numeric(10, 2), nullable=False)
    is_friendly_discount = db.Column(db.Boolean, nullable=True, default=False)
    calculation_snapshot = db.Column(db.Text, nullable=True)

    laundry_service = db.relationship("LaundryService")
    service = db.relationship("CatalogServiceLegacy")
    service_variant = db.relationship("ServiceVariantLegacy")
    garment_type = db.relationship("GarmentType")

    def __repr__(self):
        return f"<OrderItem id={self.id} laundry_service_id={self.laundry_service_id}>"
