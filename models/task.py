from db import db
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

class Task(db.Model):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(True), default=func.now())
    updated_at = Column(DateTime(True), default=func.now(), onupdate=func.now())

    user = relationship("User", backref="tasks", lazy=True)
    views = relationship("TaskView", backref="task", lazy=True)

    def __repr__(self):
        return f"<Task id={self.id} user_id={self.user_id}>"
