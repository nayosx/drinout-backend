from db import db


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    service_id = db.Column(
        db.Integer,
        db.ForeignKey("services.id", onupdate="CASCADE"),
        nullable=False,
    )
    suggested_price_option_id = db.Column(
        db.Integer,
        db.ForeignKey("service_price_options.id", onupdate="CASCADE"),
    )
    service_name_snapshot = db.Column(db.String(150), nullable=False)
    category_name_snapshot = db.Column(db.String(100), nullable=False)
    pricing_mode = db.Column(db.String(30), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    weight_lb = db.Column(db.Numeric(10, 2))
    unit_label_snapshot = db.Column(db.String(30), nullable=False)
    suggested_price_label_snapshot = db.Column(db.String(100))
    suggested_unit_price = db.Column(db.Numeric(10, 2))
    recommended_unit_price = db.Column(db.Numeric(10, 2))
    final_unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    manual_price_override_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", onupdate="CASCADE"),
    )
    manual_price_override_reason = db.Column(db.String(255))
    discount_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    subtotal_before_discount = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal_after_discount = db.Column(db.Numeric(10, 2), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    order = db.relationship("Order", back_populates="items", lazy="selectin")
    service = db.relationship("CatalogService", back_populates="order_items", lazy="selectin")
    suggested_price_option = db.relationship(
        "ServicePriceOption",
        back_populates="order_items",
        lazy="selectin",
    )
    manual_price_override_by_user = db.relationship(
        "User",
        foreign_keys=[manual_price_override_by_user_id],
        lazy="selectin",
    )
    weight_pricing_snapshot = db.relationship(
        "OrderWeightPricingSnapshot",
        back_populates="order_item",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan",
    )
