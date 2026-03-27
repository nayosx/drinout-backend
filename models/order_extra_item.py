from db import db


class OrderExtraItem(db.Model):
    __tablename__ = "order_extra_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    extra_id = db.Column(
        db.Integer,
        db.ForeignKey("extras_catalog.id", onupdate="CASCADE"),
        nullable=False,
    )
    extra_name_snapshot = db.Column(db.String(150), nullable=False)
    unit_label_snapshot = db.Column(db.String(30), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    suggested_unit_price = db.Column(db.Numeric(10, 2))
    final_unit_price = db.Column(db.Numeric(10, 2), nullable=False)
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

    order = db.relationship("Order", back_populates="extra_items", lazy="selectin")
    extra = db.relationship("ExtraCatalog", back_populates="order_extra_items", lazy="selectin")
