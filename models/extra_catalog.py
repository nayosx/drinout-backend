from db import db


class ExtraCatalog(db.Model):
    __tablename__ = "extras_catalog"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(150), unique=True, nullable=False)
    unit_label = db.Column(db.String(30), nullable=False, default="unidad")
    suggested_unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    order_extra_items = db.relationship("OrderExtraItem", back_populates="extra", lazy="selectin")
