from db import db
from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey, Text, Numeric, func
from sqlalchemy.orm import relationship

class LaundryService(db.Model):
    __tablename__ = "laundry_services"

    FULFILLMENT_TYPE_WALK_IN = "WALK_IN"
    FULFILLMENT_TYPE_DELIVERY = "DELIVERY"
    FULFILLMENT_TYPE_PICKUP_DELIVERY = "PICKUP_DELIVERY"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    client_address_id = Column(Integer, ForeignKey("client_addresses.id"), nullable=False)
    scheduled_pickup_at = Column(DateTime, nullable=False)
    pending_order = Column(Integer, nullable=True)
    status = Column(
        Enum(
            "PENDING",
            "STARTED",
            "IN_PROGRESS",
            "READY_FOR_DELIVERY",
            "DELIVERED",
            "CANCELLED",
            name="laundry_status"
        ),
        nullable=False,
        default="PENDING"
    )
    service_label = Column(Enum("NORMAL", "EXPRESS"), nullable=False, default="NORMAL")
    fulfillment_type = Column(
        db.String(20),
        nullable=True,
        default=FULFILLMENT_TYPE_WALK_IN,
    )
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    client = relationship("Client")
    client_address = relationship("ClientAddress")
    transaction = relationship("Transaction")
    created_by_user = relationship("User")

    def __repr__(self):
        return f"<LaundryService id={self.id} status={self.status}>"
