from db import db


class CatalogServiceLegacy(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("service_categories.id"),
        nullable=False,
    )
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, nullable=True, default=True)

    category = db.relationship("ServiceCategoryLegacy", back_populates="services")
    variants = db.relationship(
        "ServiceVariantLegacy",
        back_populates="service",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<CatalogServiceLegacy id={self.id} name={self.name}>"
