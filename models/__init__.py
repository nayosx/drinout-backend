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
from .refresh_token import RefreshToken
from .laundry_service import LaundryService
from .laundry_processing_step import LaundryProcessingStep
from .laundry_delivery import LaundryDelivery
from .laundry_activity_log import LaundryActivityLog
from .laundry_service_log import LaundryServiceLog
from .garment_type import GarmentType
from .global_setting import GlobalSetting
from .extra import Extra
from .service_category_legacy import ServiceCategoryLegacy
from .catalog_service_legacy import CatalogServiceLegacy
from .service_variant_legacy import ServiceVariantLegacy
