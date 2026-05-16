from db import db
from sqlalchemy import Column, Integer, DateTime, Enum, Text, ForeignKey, func
from sqlalchemy.orm import relationship

class LaundryDelivery(db.Model):
    __tablename__ = "laundry_deliveries"

    id = Column(Integer, primary_key=True)
    laundry_service_id = Column(Integer, ForeignKey("laundry_services.id"), nullable=False)
    scheduled_departure_time = Column(DateTime, nullable=False)
    actual_departure_time = Column(DateTime, nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    customer_expected_time = Column(DateTime, nullable=False)
    actual_delivery_time = Column(DateTime, nullable=True)
    status = Column(
        Enum(
            "ASSIGNED",
            "EN_ROUTE",
            "DELIVERED",
            "REJECTED",
            name="delivery_status"
        ),
        nullable=False,
        default="ASSIGNED"
    )
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    laundry_service = relationship("LaundryService")
    manager = relationship("User", foreign_keys=[manager_id])
    driver = relationship("User", foreign_keys=[driver_id])
