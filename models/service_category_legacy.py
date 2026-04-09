from db import db


class ServiceCategoryLegacy(db.Model):
    __tablename__ = "service_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, nullable=True, default=True)

    services = db.relationship(
        "CatalogServiceLegacy",
        back_populates="category",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<ServiceCategoryLegacy id={self.id} name={self.name}>"
