from db import db
from datetime import datetime

class TransactionCategory(db.Model):
    __tablename__ = 'transaction_category'

    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<TransactionCategory {self.category_name}>'
