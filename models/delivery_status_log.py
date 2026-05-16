from db import db
from sqlalchemy import Column, Integer, BigInteger, DateTime, Enum, ForeignKey, func

class DeliveryStatusLog(db.Model):
    __tablename__ = "delivery_status_logs"

    id = Column(BigInteger, primary_key=True)
    dispatch_id = Column(Integer, ForeignKey("laundry_deliveries.id"), nullable=False)
    status = Column(
        Enum(
            "ASSIGNED",
            "EN_ROUTE",
            "DELIVERED",
            "REJECTED",
            name="delivery_log_status"
        ),
        nullable=False
    )
    logged_at = Column(DateTime, default=func.now())
