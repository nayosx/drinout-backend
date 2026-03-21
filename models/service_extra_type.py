from db import db


class ServiceExtraType(db.Model):
    __tablename__ = "service_extra_types"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    unit_label = db.Column(db.String(30), nullable=False, default="unidad")
    default_unit_price = db.Column(db.Numeric(10, 2), nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    display_order = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    service_extras = db.relationship(
        "LaundryServiceExtra",
        back_populates="service_extra_type",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<ServiceExtraType id={self.id} code={self.code}>"
