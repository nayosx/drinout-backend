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
from .laundry_service_item import LaundryServiceItem
from .service_extra_type import ServiceExtraType
from .laundry_service_extra import LaundryServiceExtra
from .service_category import ServiceCategory
from .catalog_service import CatalogService
from .service_price_option import ServicePriceOption
from .extra_catalog import ExtraCatalog
from .delivery_zone import DeliveryZone, DeliveryZonePrice
from .weight_pricing_profile import WeightPricingProfile
from .weight_pricing_tier import WeightPricingTier
from .order import Order
from .order_item import OrderItem
from .order_extra_item import OrderExtraItem
from .order_status_history import OrderStatusHistory
from .order_weight_pricing_snapshot import OrderWeightPricingSnapshot
from .global_setting import GlobalSetting
from .laundry_service_commercial_draft import LaundryServiceCommercialDraft
