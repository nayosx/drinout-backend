from db import db
from sqlalchemy import Table, Column, Integer, ForeignKey

menu_roles = Table(
    "menu_roles", db.Model.metadata,
    Column("menu_id", Integer, ForeignKey("menus.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
)