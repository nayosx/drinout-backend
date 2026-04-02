from db import db


class WeightPricingProfile(db.Model):
    __tablename__ = "weight_pricing_profiles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    strategy = db.Column(db.String(40), nullable=False, default="PACKAGE_BLOCKS")
    extra_lb_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    auto_upgrade_enabled = db.Column(db.Boolean, nullable=False, default=False)
    auto_upgrade_margin = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    force_upgrade_from_lb = db.Column(db.Numeric(10, 2))
    compare_all_tiers = db.Column(db.Boolean, nullable=False, default=True)
    round_mode = db.Column(db.String(20), nullable=False, default="exact")
    allow_manual_override = db.Column(db.Boolean, nullable=False, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    tiers = db.relationship(
        "WeightPricingTier",
        back_populates="profile",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="WeightPricingTier.sort_order.asc()",
    )
    orders = db.relationship("Order", back_populates="pricing_profile", lazy="selectin")
    weight_pricing_snapshots = db.relationship(
        "OrderWeightPricingSnapshot",
        back_populates="pricing_profile",
        lazy="selectin",
    )
