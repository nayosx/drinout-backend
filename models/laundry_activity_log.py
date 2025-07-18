from db import db
from sqlalchemy import Column, Integer, Enum, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

class LaundryActivityLog(db.Model):
    __tablename__ = "laundry_activity_logs"

    id = Column(Integer, primary_key=True)
    laundry_service_id = Column(Integer, ForeignKey("laundry_services.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(Enum("CREACION", "ACTUALIZACION", "CAMBIO_ESTADO", "ANOTACION"), nullable=False)
    previous_status = Column(Enum("PENDIENTE", "EN_PROCESO", "LISTO_PARA_ENVIO", "COMPLETADO", "CANCELADO"), nullable=True)
    new_status = Column(Enum("PENDIENTE", "EN_PROCESO", "LISTO_PARA_ENVIO", "COMPLETADO", "CANCELADO"), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    laundry_service = relationship("LaundryService")
    user = relationship("User")
