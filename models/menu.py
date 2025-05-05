# models/menu.py
from db import db
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

class Menu(db.Model):
    __tablename__ = "menus"
    id = Column(Integer, primary_key=True)
    label = Column(String(100), nullable=False)
    path = Column(String(255), nullable=False)
    show_in_sidebar = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    parent_id = Column(Integer, ForeignKey("menus.id"), nullable=True)

    children = relationship("Menu", backref=db.backref("parent", remote_side=[id]))
    roles = relationship("Role", secondary="menu_roles", back_populates="menus")