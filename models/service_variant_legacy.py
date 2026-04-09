from db import db


class ServiceVariantLegacy(db.Model):
    __tablename__ = "service_variants"

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(
        db.Integer,
        db.ForeignKey("services.id"),
        nullable=False,
    )
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, nullable=True, default=True)

    service = db.relationship("CatalogServiceLegacy", back_populates="variants")

    def __repr__(self):
        return f"<ServiceVariantLegacy id={self.id} name={self.name}>"
