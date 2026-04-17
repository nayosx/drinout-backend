from db import db


class DiscountRule(db.Model):
    __tablename__ = "discount_rules"

    DISCOUNT_TYPE_PACKAGE_PRICE = "package_price"
    DISCOUNT_TYPE_PERCENTAGE = "percentage"
    DISCOUNT_TYPE_FIXED_AMOUNT = "fixed_amount"

    APPLICATION_MODE_EXACT = "exact"
    APPLICATION_MODE_ONE_TIME = "one_time"
    APPLICATION_MODE_PER_BLOCK = "per_block"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
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
    min_quantity = db.Column(db.Integer, nullable=False, default=1)
    block_quantity = db.Column(db.Integer, nullable=True)
    discount_type = db.Column(db.String(30), nullable=False)
    application_mode = db.Column(db.String(30), nullable=False, default=APPLICATION_MODE_EXACT)
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    priority = db.Column(db.Integer, nullable=False, default=1)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    starts_at = db.Column(db.DateTime, nullable=True)
    ends_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    service = db.relationship("CatalogServiceLegacy")
    service_variant = db.relationship("ServiceVariantLegacy")

    def __repr__(self):
        return f"<DiscountRule id={self.id} service_id={self.service_id} name={self.name}>"
