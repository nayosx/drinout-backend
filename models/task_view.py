from db import db
from sqlalchemy import Column, Integer, DateTime, ForeignKey, func

class TaskView(db.Model):
    __tablename__ = "task_views"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    viewed_at = Column(DateTime(True), default=func.now())

    def __repr__(self):
        return f"<TaskView id={self.id} task_id={self.task_id} user_id={self.user_id}>"
