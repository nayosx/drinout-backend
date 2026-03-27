from db import db


class CatalogService(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("service_categories.id", onupdate="CASCADE"),
        nullable=False,
    )
    code = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(150), unique=True, nullable=False)
    pricing_mode = db.Column(db.String(30), nullable=False, default="FIXED")
    unit_label = db.Column(db.String(30), nullable=False, default="unidad")
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    allow_manual_price_override = db.Column(db.Boolean, nullable=False, default=True)
    allow_item_discount = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    category = db.relationship("ServiceCategory", back_populates="services", lazy="selectin")
    price_options = db.relationship(
        "ServicePriceOption",
        back_populates="service",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    order_items = db.relationship("OrderItem", back_populates="service", lazy="selectin")
