from db import db


class DeliveryZone(db.Model):
    __tablename__ = "delivery_zones"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    prices = db.relationship(
        "DeliveryZonePrice",
        back_populates="delivery_zone",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="DeliveryZonePrice.effective_from.desc()",
    )
    orders = db.relationship("Order", back_populates="delivery_zone", lazy="selectin")


class DeliveryZonePrice(db.Model):
    __tablename__ = "delivery_zone_prices"

    id = db.Column(db.Integer, primary_key=True)
    delivery_zone_id = db.Column(
        db.Integer,
        db.ForeignKey("delivery_zones.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    fee_amount = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    effective_from = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    effective_to = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    delivery_zone = db.relationship("DeliveryZone", back_populates="prices", lazy="selectin")
    orders = db.relationship("Order", back_populates="delivery_zone_price", lazy="selectin")
