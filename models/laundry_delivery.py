from db import db
from sqlalchemy import Column, Integer, DateTime, Enum, Text, ForeignKey, func
from sqlalchemy.orm import relationship

class LaundryDelivery(db.Model):
    __tablename__ = "laundry_deliveries"

    id = Column(Integer, primary_key=True)
    laundry_service_id = Column(Integer, ForeignKey("laundry_services.id"), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    scheduled_delivery_at = Column(DateTime, nullable=False)
    delivered_at = Column(DateTime, nullable=True)
    status = Column(Enum("PENDING", "DELIVERED", "CANCELLED"), nullable=False, default="PENDING")
    cancel_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    laundry_service = relationship("LaundryService")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    assigned_to_user = relationship("User", foreign_keys=[assigned_to_user_id])
