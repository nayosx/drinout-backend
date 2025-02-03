from db import db
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, Text, func
from sqlalchemy.orm import relationship

class WorkSession(db.Model):
    __tablename__ = "work_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    login_time = Column(DateTime, default=func.now(), nullable=False)
    logout_time = Column(DateTime, nullable=True)
    status = Column(Enum("IN_PROGRESS", "COMPLETED"), default="IN_PROGRESS", nullable=False)
    comments = Column(Text, nullable=True)

    user = relationship("User", backref="work_sessions")

    def __repr__(self):
        return f"<WorkSession id={self.id} user_id={self.user_id} status={self.status}>"
