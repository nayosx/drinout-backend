# models/__init__.py
from db import db

# Importa tus modelos
from .role import Role
from .user import User
from .payment_type import PaymentType
from .transaction import Transaction
from .work_session import WorkSession
from .task import Task
from .task_view import TaskView
from .menu import Menu
from .menu_roles import menu_roles
from .transaction_category import TransactionCategory
from .client import Client, ClientAddress, ClientPhone