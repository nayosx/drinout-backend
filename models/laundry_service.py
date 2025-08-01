from db import db
from sqlalchemy import Column, Integer, DateTime, Enum, Text, ForeignKey, func
from sqlalchemy.orm import relationship

class LaundryService(db.Model):
    __tablename__ = "laundry_services"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    client_address_id = Column(Integer, ForeignKey("client_addresses.id"), nullable=False)
    scheduled_pickup_at = Column(DateTime, nullable=False)
    status = Column(Enum("PENDING", "STARTED", "IN_PROGRESS", "READY_FOR_DELIVERY", "DELIVERED", "CANCELLED", name="laundry_status"), nullable=False, default="PENDING")
    service_label = Column(Enum("NORMAL", "EXPRESS"), nullable=False, default="NORMAL")
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    client = relationship("Client")
    client_address = relationship("ClientAddress")
    transaction = relationship("Transaction")
    created_by_user = relationship("User")

    logs = relationship(
        "LaundryServiceLog",
        back_populates="laundry_service",
        order_by="LaundryServiceLog.created_at",
        cascade="all, delete-orphan"
    )


    def __repr__(self):
        return f"<LaundryService id={self.id} status={self.status}>"
