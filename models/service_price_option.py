from db import db


class ServicePriceOption(db.Model):
    __tablename__ = "service_price_options"

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(
        db.Integer,
        db.ForeignKey("services.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    label = db.Column(db.String(100), nullable=False)
    suggested_price = db.Column(db.Numeric(10, 2), nullable=False)
    sort_order = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    service = db.relationship("CatalogService", back_populates="price_options", lazy="selectin")
    order_items = db.relationship("OrderItem", back_populates="suggested_price_option", lazy="selectin")
