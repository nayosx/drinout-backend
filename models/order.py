from db import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id", onupdate="CASCADE"), nullable=False)
    client_address_id = db.Column(db.Integer, db.ForeignKey("client_addresses.id", onupdate="CASCADE"))
    pricing_profile_id = db.Column(
        db.Integer,
        db.ForeignKey("weight_pricing_profiles.id", onupdate="CASCADE"),
    )
    payment_type_id = db.Column(
        db.Integer,
        db.ForeignKey("payment_types.id", onupdate="CASCADE"),
        nullable=False,
    )
    delivery_zone_id = db.Column(
        db.Integer,
        db.ForeignKey("delivery_zones.id", onupdate="CASCADE"),
    )
    delivery_zone_price_id = db.Column(
        db.Integer,
        db.ForeignKey("delivery_zone_prices.id", onupdate="CASCADE"),
    )
    status = db.Column(db.String(40), nullable=False, default="DRAFT")
    service_subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    extras_subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    delivery_fee_suggested = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    delivery_fee_final = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    delivery_fee_override_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", onupdate="CASCADE"),
    )
    delivery_fee_override_reason = db.Column(db.String(255))
    global_discount_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    global_discount_reason = db.Column(db.String(255))
    subtotal_before_payment_surcharge = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    payment_type_name_snapshot = db.Column(db.String(100), nullable=False)
    payment_surcharge_type_snapshot = db.Column(db.String(20), nullable=False)
    payment_surcharge_value_snapshot = db.Column(db.Numeric(10, 4), nullable=False, default=0)
    payment_surcharge_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    notes = db.Column(db.Text)
    charged_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", onupdate="CASCADE"))
    created_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", onupdate="CASCADE"),
        nullable=False,
    )
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", onupdate="CASCADE"))
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    client = db.relationship("Client", lazy="selectin")
    client_address = db.relationship("ClientAddress", lazy="selectin")
    pricing_profile = db.relationship("WeightPricingProfile", back_populates="orders", lazy="selectin")
    payment_type = db.relationship("PaymentType", lazy="selectin")
    delivery_zone = db.relationship("DeliveryZone", back_populates="orders", lazy="selectin")
    delivery_zone_price = db.relationship("DeliveryZonePrice", back_populates="orders", lazy="selectin")
    charged_by_user = db.relationship("User", foreign_keys=[charged_by_user_id], lazy="selectin")
    created_by_user = db.relationship("User", foreign_keys=[created_by_user_id], lazy="selectin")
    updated_by_user = db.relationship("User", foreign_keys=[updated_by_user_id], lazy="selectin")
    delivery_fee_override_by_user = db.relationship(
        "User",
        foreign_keys=[delivery_fee_override_by_user_id],
        lazy="selectin",
    )
    items = db.relationship(
        "OrderItem",
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    extra_items = db.relationship(
        "OrderExtraItem",
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    status_history = db.relationship(
        "OrderStatusHistory",
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="OrderStatusHistory.created_at.asc()",
    )
