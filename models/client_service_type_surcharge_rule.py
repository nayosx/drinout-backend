from sqlalchemy import CheckConstraint, UniqueConstraint

from db import db


class ClientServiceTypeSurchargeRule(db.Model):
    __tablename__ = "client_service_type_surcharge_rules"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_client_service_type_surcharge_amount_non_negative"),
        CheckConstraint(
            "service_label IN ('NORMAL', 'EXPRESS')",
            name="chk_client_service_type_surcharge_service_label",
        ),
        UniqueConstraint(
            "client_id",
            "service_label",
            name="uq_client_service_type_surcharge_client_service_label",
        ),
    )

    SERVICE_LABEL_NORMAL = "NORMAL"
    SERVICE_LABEL_EXPRESS = "EXPRESS"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id", onupdate="CASCADE"),
        nullable=False,
    )
    service_label = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    notes = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    client = db.relationship("Client", back_populates="service_type_surcharge_rules")

    def __repr__(self):
        return (
            "<ClientServiceTypeSurchargeRule "
            f"id={self.id} client_id={self.client_id} service_label={self.service_label}>"
        )
