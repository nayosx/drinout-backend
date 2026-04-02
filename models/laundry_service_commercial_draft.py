from db import db


class LaundryServiceCommercialDraft(db.Model):
    __tablename__ = "laundry_service_commercial_drafts"

    id = db.Column(db.Integer, primary_key=True)
    laundry_service_id = db.Column(
        db.Integer,
        db.ForeignKey("laundry_services.id", onupdate="CASCADE"),
        nullable=True,
    )
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id", onupdate="CASCADE"),
        nullable=True,
    )
    client_address_id = db.Column(
        db.Integer,
        db.ForeignKey("client_addresses.id", onupdate="CASCADE"),
        nullable=True,
    )
    transaction_id = db.Column(
        db.Integer,
        db.ForeignKey("transactions.id", onupdate="CASCADE"),
        nullable=True,
    )
    payment_type_id = db.Column(
        db.Integer,
        db.ForeignKey("payment_types.id", onupdate="CASCADE"),
        nullable=True,
    )
    pricing_profile_id = db.Column(
        db.Integer,
        db.ForeignKey("weight_pricing_profiles.id", onupdate="CASCADE"),
        nullable=True,
    )
    status = db.Column(db.String(40), nullable=True)
    service_label = db.Column(db.String(40), nullable=True)
    scheduled_pickup_at = db.Column(db.DateTime, nullable=True)
    weight_lb = db.Column(db.Numeric(10, 2), nullable=True)
    distance_km = db.Column(db.Numeric(10, 2), nullable=True)
    delivery_price_per_km = db.Column(db.Numeric(10, 2), nullable=True)
    delivery_fee_suggested = db.Column(db.Numeric(10, 2), nullable=True)
    delivery_fee_final = db.Column(db.Numeric(10, 2), nullable=True)
    delivery_fee_override_reason = db.Column(db.String(255), nullable=True)
    global_discount_amount = db.Column(db.Numeric(10, 2), nullable=True)
    global_discount_reason = db.Column(db.String(255), nullable=True)
    quoted_service_amount = db.Column(db.Numeric(10, 2), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    payload_json = db.Column(db.Text, nullable=False)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    charged_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", onupdate="CASCADE"),
        nullable=True,
    )
    created_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", onupdate="CASCADE"),
        nullable=False,
    )
    updated_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", onupdate="CASCADE"),
        nullable=True,
    )
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

