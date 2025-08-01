from db import db
from sqlalchemy import Column, Integer, DateTime, Enum, Text, ForeignKey, func
from sqlalchemy.orm import relationship

class LaundryServiceLog(db.Model):
    __tablename__ = "laundry_service_logs"

    id = Column(Integer, primary_key=True)
    laundry_service_id = Column(Integer, ForeignKey("laundry_services.id"), nullable=False)
    status = Column(Enum(
        "PENDING", "STARTED", "IN_PROGRESS", "READY_FOR_DELIVERY", "DELIVERED", "CANCELLED",
        name="log_status"
    ), nullable=False)
    detail = Column(Text, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())

    created_by = relationship("User")
    laundry_service = relationship("LaundryService", back_populates="logs")

    def __repr__(self):
        return f"<LaundryServiceLog id={self.id} status={self.status}>"
