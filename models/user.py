from db import db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

class User(db.Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    role = relationship("Role", backref="users", lazy=True)
    name = Column(String(100), default="User Generic", nullable=False)
    phone = Column(String(20), default="7777-7777", nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"
