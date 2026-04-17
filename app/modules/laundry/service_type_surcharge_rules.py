from decimal import Decimal

from models.client_service_type_surcharge_rule import ClientServiceTypeSurchargeRule
from models.global_setting import GlobalSetting
from models.laundry_service import LaundryService


def load_system_service_type_surcharge(service_label: str) -> Decimal:
    normalized_service_label = (service_label or "NORMAL").strip().upper()
    if normalized_service_label != ClientServiceTypeSurchargeRule.SERVICE_LABEL_EXPRESS:
        return Decimal("0.00")

    setting = GlobalSetting.query.filter_by(
        key="express_service_surcharge",
        is_active=True,
    ).first()
    if not setting:
        raise ValueError("express_service_surcharge setting is not configured")
    return Decimal(str(setting.value)).quantize(Decimal("0.01"))


def resolve_client_service_type_surcharge(client_id: int, service_label: str) -> Decimal:
    normalized_service_label = (service_label or "NORMAL").strip().upper()
    rule = (
        ClientServiceTypeSurchargeRule.query
        .filter_by(
            client_id=client_id,
            service_label=normalized_service_label,
            is_active=True,
        )
        .order_by(ClientServiceTypeSurchargeRule.id.desc())
        .first()
    )
    if rule:
        return Decimal(str(rule.amount)).quantize(Decimal("0.01"))
    return load_system_service_type_surcharge(normalized_service_label)


def resolve_laundry_service_type_surcharge(laundry_service_id: int, service_label: str) -> Decimal:
    client_id = (
        LaundryService.query
        .with_entities(LaundryService.client_id)
        .filter(LaundryService.id == laundry_service_id)
        .scalar()
    )
    if client_id is None:
        raise ValueError("Laundry service not found")
    return resolve_client_service_type_surcharge(client_id, service_label)
