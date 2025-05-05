# models/role.py
from db import db
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

class Role(db.Model):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


    menus = relationship(
        "Menu",
        secondary="menu_roles",
        back_populates="roles",
        order_by="Menu.order"
    )

    def __repr__(self):
        return f"<Role {self.name}>"

