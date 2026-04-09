from db import db


GLOBAL_SETTING_CATEGORIES = [
    "general",
    "laundry_pricing",
    "delivery_pricing",
    "operations_workforce",
    "billing",
    "discounts",
    "integrations",
]


class GlobalSetting(db.Model):
    __tablename__ = "global_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False, unique=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255))
    category = db.Column(db.String(50), nullable=False, default="general")
    value_type = db.Column(db.String(20), nullable=False, default="STRING")
    value = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )
