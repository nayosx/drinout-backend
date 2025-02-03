# models/__init__.py
from db import db

# Importa tus modelos
from .role import Role
from .user import User
from .payment_type import PaymentType
from .transaction import Transaction
from .work_session import WorkSession