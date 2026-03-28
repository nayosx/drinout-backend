from db import db
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, func

class PaymentType(db.Model):
    __tablename__ = "payment_types"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    surcharge_type = Column(String(20), nullable=False, default="PERCENT")
    surcharge_value = Column(Numeric(10, 4), nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<PaymentType id={self.id} name={self.name}>"
