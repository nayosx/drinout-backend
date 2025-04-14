from db import db
from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, Enum, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TEXT

class Transaction(db.Model):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    transaction_type = Column(Enum("IN","OUT"), nullable=False)
    payment_type_id = Column(Integer, ForeignKey("payment_types.id"), nullable=False)
    detail = db.Column(TEXT, nullable=True)
    amount = Column(DECIMAL(10,2), nullable=False)
    created_at = Column(DateTime(True), default=func.now())
    updated_at = Column(DateTime(True), default=func.now(), onupdate=func.now())

    # Relaciones
    user = relationship("User", backref="transactions", lazy=True)
    payment_type = relationship("PaymentType", backref="transactions", lazy=True)

    def __repr__(self):
        return f"<Transaction id={self.id} type={self.transaction_type} amount={self.amount}>"
