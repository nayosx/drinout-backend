from db import db


class OrderWeightPricingSnapshot(db.Model):
    __tablename__ = "order_weight_pricing_snapshot"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    order_item_id = db.Column(
        db.Integer,
        db.ForeignKey("order_items.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        unique=True,
    )
    pricing_profile_id = db.Column(
        db.Integer,
        db.ForeignKey("weight_pricing_profiles.id", onupdate="CASCADE"),
    )
    pricing_profile_name_snapshot = db.Column(db.String(120), nullable=False)
    strategy_applied = db.Column(db.String(40), nullable=False)
    weight_lb = db.Column(db.Numeric(10, 2), nullable=False)
    selected_tier_id = db.Column(db.Integer)
    selected_tier_max_weight_lb = db.Column(db.Numeric(10, 2))
    selected_base_price = db.Column(db.Numeric(10, 2))
    recommended_price = db.Column(db.Numeric(10, 2), nullable=False)
    final_price = db.Column(db.Numeric(10, 2), nullable=False)
    override_applied = db.Column(db.Boolean, nullable=False, default=False)
    override_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", onupdate="CASCADE"))
    override_reason = db.Column(db.String(255))
    allow_manual_override = db.Column(db.Boolean, nullable=False, default=False)
    decision_reason = db.Column(db.Text, nullable=False)
    options_evaluated_json = db.Column(db.Text, nullable=False)
    lowest_valid_price = db.Column(db.Numeric(10, 2), nullable=False)
    highest_valid_price = db.Column(db.Numeric(10, 2), nullable=False)
    difference_selected_vs_lowest = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    difference_selected_vs_highest = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    order = db.relationship("Order", lazy="selectin")
    order_item = db.relationship("OrderItem", back_populates="weight_pricing_snapshot", lazy="selectin")
    pricing_profile = db.relationship(
        "WeightPricingProfile",
        back_populates="weight_pricing_snapshots",
        lazy="selectin",
    )
    override_by_user = db.relationship("User", lazy="selectin")
