from db import db
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship


class UserShortcut(db.Model):
    __tablename__ = "user_shortcuts"
    __table_args__ = (
        UniqueConstraint("user_id", "shortcut_key", name="uq_user_shortcuts_user_key"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    shortcut_key = Column(String(100), nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="shortcuts")

    def __repr__(self):
        return f"<UserShortcut user_id={self.user_id} shortcut_key={self.shortcut_key}>"
