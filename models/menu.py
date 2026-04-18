# models/menu.py
from db import db
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

class Menu(db.Model):
    __tablename__ = "menus"
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    label = Column(String(100), nullable=False)
    path = Column(String(255), nullable=True)
    icon = Column(String(100), nullable=True)
    show_in_sidebar = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    parent_id = Column(Integer, ForeignKey("menus.id"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    children = relationship("Menu", backref=db.backref("parent", remote_side=[id]))
    roles = relationship("Role", secondary="menu_roles", back_populates="menus")
