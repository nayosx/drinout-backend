# models/payment_type.py

from db import db
from sqlalchemy import Column, Integer, String, DateTime, func

class PaymentType(db.Model):
    __tablename__ = "payment_types"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<PaymentType id={self.id} name={self.name}>"
