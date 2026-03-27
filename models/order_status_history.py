from db import db


class OrderStatusHistory(db.Model):
    __tablename__ = "order_status_history"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    previous_status = db.Column(db.String(40))
    new_status = db.Column(db.String(40), nullable=False)
    changed_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", onupdate="CASCADE"),
        nullable=False,
    )
    reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    order = db.relationship("Order", back_populates="status_history", lazy="selectin")
    changed_by_user = db.relationship("User", lazy="selectin")
