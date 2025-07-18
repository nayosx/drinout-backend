from db import db
from sqlalchemy import Column, Integer, Enum, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

class LaundryProcessingStep(db.Model):
    __tablename__ = "laundry_processing_steps"

    id = Column(Integer, primary_key=True)
    laundry_service_id = Column(Integer, ForeignKey("laundry_services.id"), nullable=False)
    step_type = Column(Enum("LAVADO", "PLANCHADO", "AMBOS"), nullable=False, default="LAVADO")
    started_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    completed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    laundry_service = relationship("LaundryService")
    started_by_user = relationship("User", foreign_keys=[started_by_user_id])
    completed_by_user = relationship("User", foreign_keys=[completed_by_user_id])
