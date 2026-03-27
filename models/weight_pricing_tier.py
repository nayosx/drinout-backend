from db import db


class WeightPricingTier(db.Model):
    __tablename__ = "weight_pricing_tiers"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(
        db.Integer,
        db.ForeignKey("weight_pricing_profiles.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    max_weight_lb = db.Column(db.Numeric(10, 2), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    profile = db.relationship("WeightPricingProfile", back_populates="tiers", lazy="selectin")
