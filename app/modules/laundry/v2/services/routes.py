import json
from decimal import Decimal, ROUND_HALF_UP

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from app.modules.laundry.queue.events import emit_queue_updated
from app.services.weight_pricing import calculate_weight_service_quote
from db import db
from models.catalog_service_legacy import CatalogServiceLegacy
from models.client import Client, ClientAddress
from models.extra import Extra
from models.global_setting import GlobalSetting
from models.garment_type import GarmentType
from models.laundry_activity_log import LaundryActivityLog
from models.laundry_service import LaundryService
from models.laundry_service_extra import LaundryServiceExtra
from models.order_item import OrderItem
from models.service_category_legacy import ServiceCategoryLegacy
from models.service_variant_legacy import ServiceVariantLegacy
from schemas.laundry_service_v2_schema import LaundryServiceV2Schema, LaundryServiceV2UpsertSchema


laundry_service_v2_bp = Blueprint("laundry_service_v2_bp", __name__, url_prefix="/v2/laundry_services")

schema = LaundryServiceV2Schema()
schema_many = LaundryServiceV2Schema(many=True)
upsert_schema = LaundryServiceV2UpsertSchema()


def map_status_to_log_enum(status):
    return {
        "PENDING": "PENDIENTE",
        "IN_PROGRESS": "EN_PROCESO",
        "READY_FOR_DELIVERY": "LISTO_PARA_ENVIO",
        "DELIVERED": "COMPLETADO",
        "CANCELLED": "CANCELADO",
    }.get(status)


def _get_socketio():
    return current_app.extensions.get("socketio")


def _sync_pending_order_for_status(item):
    if item.status != "PENDING":
        item.pending_order = None


def _next_pending_order():
    current_max = db.session.query(func.max(LaundryService.pending_order)).filter(
        LaundryService.status == "PENDING"
    ).scalar()
    return (current_max or 0) + 1


def _emit_queue_for_status_and_all(socketio, statuses):
    if not socketio:
        return

    unique_statuses = []
    seen_statuses = set()
    for status in statuses:
        if not status or status in seen_statuses:
            continue
        seen_statuses.add(status)
        unique_statuses.append(status)

    emit_queue_updated(
        socketio,
        statuses=None,
        include_global_room=True,
        include_client_room=False,
    )
    for status in unique_statuses:
        emit_queue_updated(
            socketio,
            statuses=[status],
            include_global_room=True,
            include_client_room=False,
        )


def _as_money(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        decimal_value = value
    else:
        decimal_value = Decimal(str(value))
    return decimal_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _line_subtotal(quantity, unit_price):
    if unit_price is None:
        return None
    return _as_money(Decimal(str(quantity)) * Decimal(str(unit_price)))


def _validate_client_and_address(client_id, client_address_id):
    client = Client.query.get(client_id)
    if not client:
        return None, None, ({"error": "Client not found"}, 404)

    address = ClientAddress.query.get(client_address_id)
    if not address or address.client_id != client_id:
        return None, None, ({"error": "Address does not belong to client"}, 400)

    return client, address, None


def _service_query():
    return LaundryService.query.options(
        selectinload(LaundryService.client),
        selectinload(LaundryService.client_address),
        selectinload(LaundryService.transaction),
        selectinload(LaundryService.created_by_user),
    )


def _load_weight_pricing_config():
    setting_keys = [
        "laundry_weight_tier_1_max_lb",
        "laundry_weight_tier_1_price",
        "laundry_weight_tier_2_max_lb",
        "laundry_weight_tier_2_price",
        "laundry_weight_extra_lb_price",
        "laundry_weight_min_price_no_services",
    ]
    rows = GlobalSetting.query.filter(
        GlobalSetting.key.in_(setting_keys),
        GlobalSetting.is_active.is_(True),
    ).all()
    by_key = {row.key: row.value for row in rows}
    return {
        "tier_1_max_lb": by_key.get("laundry_weight_tier_1_max_lb"),
        "tier_1_price": by_key.get("laundry_weight_tier_1_price"),
        "tier_2_max_lb": by_key.get("laundry_weight_tier_2_max_lb"),
        "tier_2_price": by_key.get("laundry_weight_tier_2_price"),
        "extra_lb_price": by_key.get("laundry_weight_extra_lb_price"),
        "min_price_no_services": by_key.get("laundry_weight_min_price_no_services"),
    }


def _load_delivery_price_per_km():
    setting = GlobalSetting.query.filter_by(
        key="delivery_price_per_km",
        is_active=True,
    ).first()
    if not setting:
        raise ValueError("delivery_price_per_km setting is not configured")
    return _as_money(setting.value)


def _load_express_service_surcharge():
    setting = GlobalSetting.query.filter_by(
        key="express_service_surcharge",
        is_active=True,
    ).first()
    if not setting:
        raise ValueError("express_service_surcharge setting is not configured")
    return _as_money(setting.value)


def _build_default_delivery_order_item(laundry_service_id: int):
    delivery_service = (
        CatalogServiceLegacy.query
        .filter_by(
            pricing_mode=CatalogServiceLegacy.PRICING_MODE_DELIVERY,
            is_active=True,
        )
        .order_by(CatalogServiceLegacy.id.asc())
        .first()
    )
    if not delivery_service:
        raise ValueError("Delivery service catalog is not configured")

    return OrderItem(
        laundry_service_id=laundry_service_id,
        service_id=delivery_service.id,
        service_variant_id=None,
        garment_type_id=None,
        quantity=1,
        catalog_price=0,
        applied_price=0,
        is_friendly_discount=False,
        calculation_snapshot=None,
    )


def _resolve_service_type_catalog():
    service = (
        CatalogServiceLegacy.query
        .join(ServiceCategoryLegacy, CatalogServiceLegacy.category_id == ServiceCategoryLegacy.id)
        .filter(
            func.lower(ServiceCategoryLegacy.name).in_(["surcharge", "recargo"])
        )
        .filter(CatalogServiceLegacy.is_active.is_(True))
        .order_by(CatalogServiceLegacy.id.asc())
        .first()
    )
    if not service:
        raise ValueError("Service type surcharge catalog is not configured")
    return service


def _service_type_snapshot(service_label: str):
    normalized_service_label = (service_label or "NORMAL").strip().upper()
    return (
        f'{{"service_label":"{normalized_service_label}","source":"service_label"}}'
    )


def _service_type_amount(service_label: str):
    normalized_service_label = (service_label or "NORMAL").strip().upper()
    if normalized_service_label == "EXPRESS":
        return _load_express_service_surcharge()
    return Decimal("0.00")


def _build_default_service_type_order_item(laundry_service_id: int, service_label: str):
    service_type_catalog = _resolve_service_type_catalog()
    surcharge_amount = _service_type_amount(service_label)

    return OrderItem(
        laundry_service_id=laundry_service_id,
        service_id=service_type_catalog.id,
        service_variant_id=None,
        garment_type_id=None,
        quantity=1,
        catalog_price=surcharge_amount,
        applied_price=surcharge_amount,
        is_friendly_discount=False,
        calculation_snapshot=_service_type_snapshot(service_label),
    )


def _sync_service_type_order_item(laundry_service_id: int, service_label: str):
    service_type_catalog = _resolve_service_type_catalog()
    surcharge_amount = _service_type_amount(service_label)

    item = (
        OrderItem.query
        .filter_by(
            laundry_service_id=laundry_service_id,
            service_id=service_type_catalog.id,
        )
        .order_by(OrderItem.id.asc())
        .first()
    )
    if item is None:
        item = OrderItem(
            laundry_service_id=laundry_service_id,
            service_id=service_type_catalog.id,
            service_variant_id=None,
            garment_type_id=None,
            quantity=1,
            is_friendly_discount=False,
        )
        db.session.add(item)

    item.service_variant_id = None
    item.garment_type_id = None
    item.quantity = 1
    item.catalog_price = surcharge_amount
    item.applied_price = surcharge_amount
    item.is_friendly_discount = False
    item.calculation_snapshot = _service_type_snapshot(service_label)


def _apply_nested_rows(service, data):
    try:
        _sync_service_type_order_item(service.id, service.service_label)
        _sync_delivery_order_item(
            service.id,
            service.fulfillment_type,
        )
    except ValueError as exc:
        return {"error": str(exc)}, 400
    return None


def _resolve_delivery_catalog():
    service = (
        CatalogServiceLegacy.query
        .filter_by(
            pricing_mode=CatalogServiceLegacy.PRICING_MODE_DELIVERY,
            is_active=True,
        )
        .order_by(CatalogServiceLegacy.id.asc())
        .first()
    )
    if not service:
        raise ValueError("Delivery service catalog is not configured")
    return service


def _resolve_weight_service_catalog():
    service = (
        CatalogServiceLegacy.query
        .filter_by(
            pricing_mode=CatalogServiceLegacy.PRICING_MODE_WEIGHT,
            is_active=True,
        )
        .order_by(CatalogServiceLegacy.id.asc())
        .first()
    )
    if not service:
        raise ValueError("Weight service catalog is not configured")
    return service


def _snapshot_to_dict(snapshot):
    if snapshot is None:
        return None
    if isinstance(snapshot, dict):
        return snapshot
    if isinstance(snapshot, str):
        try:
            return json.loads(snapshot)
        except json.JSONDecodeError:
            return {"raw": snapshot}
    return None


def _snapshot_to_text(snapshot):
    if snapshot is None or isinstance(snapshot, str):
        return snapshot
    return json.dumps(snapshot, ensure_ascii=True)


def _as_bool(value, field_name):
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        if value in (0, 1):
            return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("true", "1", "yes"):
            return True
        if normalized in ("false", "0", "no"):
            return False
    raise ValueError(f"{field_name} must be boolean")


def _serialize_decimal(value):
    if value is None:
        return None
    return f"{_as_money(value):.2f}"


def _order_item_payload(item):
    return {
        "id": item.id,
        "service_id": item.service_id,
        "service_name": item.service.name if item.service else None,
        "service_category_name": (
            item.service.category.name
            if item.service and item.service.category
            else None
        ),
        "pricing_mode": item.service.pricing_mode if item.service else None,
        "service_variant_id": item.service_variant_id,
        "service_variant_name": item.service_variant.name if item.service_variant else None,
        "garment_type_id": item.garment_type_id,
        "garment_type_name": item.garment_type.name if item.garment_type else None,
        "quantity": _serialize_decimal(item.quantity),
        "catalog_price": _serialize_decimal(item.catalog_price),
        "applied_price": _serialize_decimal(item.applied_price),
        "is_friendly_discount": bool(item.is_friendly_discount),
        "calculation_snapshot": _snapshot_to_dict(item.calculation_snapshot),
    }


def _extra_payload(item):
    return {
        "id": item.id,
        "extra_id": item.extra_id,
        "extra_name": item.extra.name if item.extra else None,
        "quantity": item.quantity,
        "unit_price": _serialize_decimal(item.unit_price),
        "subtotal": _serialize_decimal(item.subtotal),
        "is_courtesy": bool(item.is_courtesy),
    }


def _load_summary_order_items(laundry_service_id):
    return (
        OrderItem.query.options(
            selectinload(OrderItem.service).selectinload(CatalogServiceLegacy.category),
            selectinload(OrderItem.service_variant),
            selectinload(OrderItem.garment_type),
        )
        .filter(OrderItem.laundry_service_id == laundry_service_id)
        .order_by(OrderItem.id.asc())
        .all()
    )


def _load_summary_extras(laundry_service_id):
    return (
        LaundryServiceExtra.query.options(
            selectinload(LaundryServiceExtra.extra),
        )
        .filter(LaundryServiceExtra.laundry_service_id == laundry_service_id)
        .order_by(LaundryServiceExtra.id.asc())
        .all()
    )


def _automatic_service_ids():
    ids = set()
    ids.add(_resolve_delivery_catalog().id)
    ids.add(_resolve_service_type_catalog().id)
    return ids


def _build_weight_service_detail(item):
    payload = _order_item_payload(item)
    snapshot = payload["calculation_snapshot"] or {}
    garments = snapshot.get("garments") or []
    garment_ids = [
        garment.get("garment_type_id")
        for garment in garments
        if garment.get("garment_type_id") is not None
    ]
    garment_map = {
        row.id: row
        for row in GarmentType.query.filter(GarmentType.id.in_(garment_ids)).all()
    } if garment_ids else {}

    payload["weight_lb"] = (
        snapshot.get("weight_lb")
        if snapshot.get("weight_lb") is not None
        else snapshot.get("breakdown", {}).get("total_weight")
    )
    payload["has_other_services"] = (
        snapshot.get("has_other_services")
        if snapshot.get("has_other_services") is not None
        else snapshot.get("breakdown", {}).get("has_other_services")
    )
    payload["quote"] = snapshot.get("quote")
    payload["garments"] = [
        {
            "garment_type_id": garment.get("garment_type_id"),
            "garment_type_name": (
                garment_map.get(garment.get("garment_type_id")).name
                if garment.get("garment_type_id") in garment_map
                else None
            ),
            "quantity": garment.get("quantity"),
        }
        for garment in garments
    ]
    return payload


def _build_summary_response(service):
    items = _load_summary_order_items(service.id)
    extras = _load_summary_extras(service.id)
    automatic_ids = _automatic_service_ids()

    automatic_items = []
    manual_items = []
    weight_service_detail = None

    automatic_subtotal = Decimal("0.00")
    manual_subtotal = Decimal("0.00")
    weight_subtotal = Decimal("0.00")
    extras_subtotal = Decimal("0.00")

    for item in items:
        if item.service_id in automatic_ids:
            automatic_items.append(_order_item_payload(item))
            automatic_subtotal += _as_money(item.applied_price or 0)
            continue
        if item.service and item.service.pricing_mode == CatalogServiceLegacy.PRICING_MODE_WEIGHT:
            weight_service_detail = _build_weight_service_detail(item)
            weight_subtotal += _as_money(item.applied_price or 0)
            continue
        manual_items.append(_order_item_payload(item))
        manual_subtotal += _as_money(item.applied_price or 0)

    extra_payloads = []
    for extra in extras:
        extra_payloads.append(_extra_payload(extra))
        extras_subtotal += _as_money(extra.subtotal or 0)

    grand_total = _as_money(
        automatic_subtotal + manual_subtotal + weight_subtotal + extras_subtotal
    )

    return {
        "laundry_service": {
            "id": service.id,
            "scheduled_pickup_at": service.scheduled_pickup_at.isoformat() if service.scheduled_pickup_at else None,
            "status": service.status,
            "service_label": service.service_label,
            "fulfillment_type": service.fulfillment_type,
            "transaction_id": service.transaction_id,
            "notes": service.notes,
        },
        "client": {
            "id": service.client.id if service.client else None,
            "name": service.client.name if service.client else None,
        },
        "client_phones": [
            {
                "id": phone.id,
                "phone_number": phone.phone_number,
                "is_primary": bool(phone.is_primary),
            }
            for phone in sorted(
                service.client.phones if service.client else [],
                key=lambda phone: (not bool(phone.is_primary), phone.id),
            )
        ],
        "client_address": {
            "id": service.client_address.id if service.client_address else None,
            "address_text": service.client_address.address_text if service.client_address else None,
            "latitude": _serialize_decimal(service.client_address.latitude) if service.client_address else None,
            "longitude": _serialize_decimal(service.client_address.longitude) if service.client_address else None,
            "map_link": service.client_address.map_link if service.client_address else None,
            "image_path": service.client_address.image_path if service.client_address else None,
            "is_primary": bool(service.client_address.is_primary) if service.client_address else False,
        },
        "automatic_items": automatic_items,
        "weight_service_detail": weight_service_detail,
        "manual_items": manual_items,
        "extras": extra_payloads,
        "summary": {
            "automatic_items_subtotal": f"{automatic_subtotal:.2f}",
            "weight_service_subtotal": f"{weight_subtotal:.2f}",
            "manual_items_subtotal": f"{manual_subtotal:.2f}",
            "extras_subtotal": f"{extras_subtotal:.2f}",
            "grand_total": f"{grand_total:.2f}",
        },
    }


def _sync_delivery_order_item(
    laundry_service_id,
    fulfillment_type,
    distance_km=None,
    manual_delivery_fee=None,
):
    delivery_service = _resolve_delivery_catalog()
    normalized_fulfillment_type = (fulfillment_type or "").strip().upper()
    if normalized_fulfillment_type not in {
        LaundryService.FULFILLMENT_TYPE_WALK_IN,
        LaundryService.FULFILLMENT_TYPE_DELIVERY,
        LaundryService.FULFILLMENT_TYPE_PICKUP_DELIVERY,
    }:
        raise ValueError("fulfillment_type must be one of WALK_IN, DELIVERY, PICKUP_DELIVERY")

    if manual_delivery_fee is not None:
        manual_delivery_fee = _as_money(manual_delivery_fee)
        if manual_delivery_fee < 0:
            raise ValueError("manual_delivery_fee cannot be negative")

    if distance_km is not None:
        distance_km = _as_money(distance_km)
        if distance_km < 0:
            raise ValueError("distance_km cannot be negative")

    item = (
        OrderItem.query
        .filter_by(
            laundry_service_id=laundry_service_id,
            service_id=delivery_service.id,
        )
        .order_by(OrderItem.id.asc())
        .first()
    )
    if item is None:
        item = _build_default_delivery_order_item(laundry_service_id)
        db.session.add(item)

    existing_snapshot = _snapshot_to_dict(item.calculation_snapshot) or {}
    snapshot_distance = existing_snapshot.get("distance_km")
    if distance_km is None and snapshot_distance is not None:
        distance_km = _as_money(snapshot_distance)

    if normalized_fulfillment_type == LaundryService.FULFILLMENT_TYPE_WALK_IN:
        if manual_delivery_fee is not None and manual_delivery_fee > 0:
            raise ValueError(
                "Cannot charge delivery when fulfillment_type is WALK_IN. "
                "Change fulfillment_type to DELIVERY or PICKUP_DELIVERY."
            )
        item.service_variant_id = None
        item.garment_type_id = None
        item.quantity = 1
        item.catalog_price = Decimal("0.00")
        item.applied_price = Decimal("0.00")
        item.is_friendly_discount = False
        item.calculation_snapshot = _snapshot_to_text(
            {
                "fulfillment_type": normalized_fulfillment_type,
                "distance_km": f"{distance_km:.2f}" if distance_km is not None else None,
                "final_delivery_fee": "0.00",
                "is_manual_override": False,
            }
        )
        return item

    final_delivery_fee = item.applied_price or Decimal("0.00")
    suggested_delivery_fee = existing_snapshot.get("suggested_delivery_fee")
    delivery_price_per_km = existing_snapshot.get("delivery_price_per_km")

    if distance_km is not None:
        delivery_price_per_km_money = _load_delivery_price_per_km()
        if normalized_fulfillment_type == LaundryService.FULFILLMENT_TYPE_DELIVERY:
            suggested_money = _as_money((distance_km * delivery_price_per_km_money) / Decimal("2"))
        else:
            suggested_money = _as_money(distance_km * delivery_price_per_km_money)
        suggested_delivery_fee = f"{suggested_money:.2f}"
        delivery_price_per_km = f"{delivery_price_per_km_money:.2f}"
        final_delivery_fee = suggested_money

    if manual_delivery_fee is not None:
        final_delivery_fee = manual_delivery_fee

    item.service_variant_id = None
    item.garment_type_id = None
    item.quantity = 1
    item.catalog_price = final_delivery_fee
    item.applied_price = final_delivery_fee
    item.is_friendly_discount = False
    item.calculation_snapshot = _snapshot_to_text(
        {
            "fulfillment_type": normalized_fulfillment_type,
            "distance_km": f"{distance_km:.2f}" if distance_km is not None else snapshot_distance,
            "delivery_price_per_km": delivery_price_per_km,
            "suggested_delivery_fee": suggested_delivery_fee,
            "manual_delivery_fee": (
                f"{manual_delivery_fee:.2f}" if manual_delivery_fee is not None else None
            ),
            "final_delivery_fee": f"{_as_money(final_delivery_fee):.2f}",
            "is_manual_override": manual_delivery_fee is not None,
        }
    )
    return item


def _validate_fixed_order_item_payload(data):
    service_id = data.get("service_id")
    if service_id is None:
        raise ValueError("service_id is required")

    service = CatalogServiceLegacy.query.get(service_id)
    if not service or not service.is_active:
        raise ValueError("Service not found")
    if service.pricing_mode != CatalogServiceLegacy.PRICING_MODE_FIXED:
        raise ValueError(
            "order_items only accepts FIXED services. Use weight_service for WEIGHT and header for DELIVERY."
        )

    quantity = _as_money(data.get("quantity"))
    if quantity is None or quantity <= 0:
        raise ValueError("quantity must be greater than zero")

    catalog_price = _as_money(data.get("catalog_price"))
    applied_price = _as_money(data.get("applied_price"))
    if catalog_price is None or catalog_price < 0:
        raise ValueError("catalog_price must be zero or greater")
    if applied_price is None or applied_price < 0:
        raise ValueError("applied_price must be zero or greater")

    service_variant_id = data.get("service_variant_id")
    if data.get("garment_type_id") is not None:
        raise ValueError("garment_type_id only applies to WEIGHT services")
    variant = None
    if service_variant_id is not None:
        variant = ServiceVariantLegacy.query.get(service_variant_id)
        if not variant or variant.service_id != service.id:
            raise ValueError("service_variant_id does not belong to service_id")

    return {
        "service": service,
        "service_variant": variant,
        "quantity": quantity,
        "catalog_price": catalog_price,
        "applied_price": applied_price,
        "is_friendly_discount": bool(data.get("is_friendly_discount", False)),
        "calculation_snapshot": _snapshot_to_text(data.get("calculation_snapshot")),
    }


def _build_fixed_order_items(laundry_service_id, rows):
    seen = set()
    items = []
    for row in rows:
        normalized = _validate_fixed_order_item_payload(row)
        key = (
            normalized["service"].id,
            normalized["service_variant"].id if normalized["service_variant"] else None,
        )
        if key in seen:
            raise ValueError("Duplicate FIXED service row in order_items payload")
        seen.add(key)
        items.append(
            OrderItem(
                laundry_service_id=laundry_service_id,
                service_id=normalized["service"].id,
                service_variant_id=(
                    normalized["service_variant"].id if normalized["service_variant"] else None
                ),
                garment_type_id=None,
                quantity=normalized["quantity"],
                catalog_price=normalized["catalog_price"],
                applied_price=normalized["applied_price"],
                is_friendly_discount=normalized["is_friendly_discount"],
                calculation_snapshot=normalized["calculation_snapshot"],
            )
        )
    return items


def _build_weight_order_item(laundry_service_id, weight_payload, default_has_other_services):
    weight_service = _resolve_weight_service_catalog()
    weight_lb = weight_payload.get("weight_lb")
    if weight_lb is None:
        raise ValueError("weight_service.weight_lb is required")

    garments = weight_payload.get("garments")
    if garments is None:
        garments = []
    if not isinstance(garments, list):
        raise ValueError("weight_service.garments must be a list")

    seen_garment_ids = set()
    normalized_garments = []
    for garment in garments:
        garment_type_id = garment.get("garment_type_id")
        if garment_type_id is None:
            raise ValueError("garment_type_id is required in weight_service.garments")
        if garment_type_id in seen_garment_ids:
            raise ValueError("Duplicate garment_type_id in weight_service.garments")
        garment_type = GarmentType.query.get(garment_type_id)
        if not garment_type:
            raise ValueError("Garment type not found")
        quantity = _as_money(garment.get("quantity"))
        if quantity is None or quantity <= 0:
            raise ValueError("weight_service garment quantity must be greater than zero")
        seen_garment_ids.add(garment_type_id)
        normalized_garments.append(
            {
                "garment_type_id": garment_type_id,
                "quantity": f"{quantity:.2f}",
            }
        )

    has_other_services_raw = weight_payload.get("has_other_services")
    if has_other_services_raw is None:
        has_other_services = default_has_other_services
    else:
        has_other_services = _as_bool(has_other_services_raw, "weight_service.has_other_services")

    quote = calculate_weight_service_quote(
        weight_lb=weight_lb,
        has_other_services=has_other_services,
        pricing_config=_load_weight_pricing_config(),
    )
    final_price = _as_money(quote["summary"]["final_price"])
    return OrderItem(
        laundry_service_id=laundry_service_id,
        service_id=weight_service.id,
        service_variant_id=None,
        garment_type_id=None,
        quantity=Decimal("1.00"),
        catalog_price=final_price,
        applied_price=final_price,
        is_friendly_discount=bool(quote["summary"]["is_friendly_applied"]),
        calculation_snapshot=_snapshot_to_text(
            {
                "weight_lb": f"{_as_money(weight_lb):.2f}",
                "has_other_services": has_other_services,
                "garments": normalized_garments,
                "quote": quote,
            }
        ),
    )


def _replace_manual_order_items(service, data):
    rows = data.get("order_items")
    weight_payload = data.get("weight_service")
    if rows is None and weight_payload is None:
        return

    if rows is not None and not isinstance(rows, list):
        raise ValueError("order_items must be a list")
    if weight_payload is not None and not isinstance(weight_payload, dict):
        raise ValueError("weight_service must be an object")

    automatic_ids = _automatic_service_ids()
    (
        OrderItem.query
        .filter(OrderItem.laundry_service_id == service.id)
        .filter(~OrderItem.service_id.in_(automatic_ids))
        .delete(synchronize_session=False)
    )

    fixed_items = _build_fixed_order_items(service.id, rows or [])
    for item in fixed_items:
        db.session.add(item)

    if weight_payload is not None:
        weight_item = _build_weight_order_item(
            service.id,
            weight_payload,
            default_has_other_services=bool(fixed_items),
        )
        db.session.add(weight_item)


def _replace_extras(service, rows):
    if rows is None:
        return
    if not isinstance(rows, list):
        raise ValueError("extras must be a list")

    seen_extra_ids = set()
    (
        LaundryServiceExtra.query
        .filter(LaundryServiceExtra.laundry_service_id == service.id)
        .delete(synchronize_session=False)
    )

    for row in rows:
        extra_id = row.get("extra_id")
        if extra_id is None:
            raise ValueError("extra_id is required")
        if extra_id in seen_extra_ids:
            raise ValueError("Duplicate extra_id in extras payload")
        extra = Extra.query.get(extra_id)
        if not extra or not extra.is_active:
            raise ValueError("Extra not found")
        quantity = row.get("quantity")
        if quantity is None or int(quantity) <= 0:
            raise ValueError("extra quantity must be greater than zero")
        unit_price = _as_money(row.get("unit_price"))
        if unit_price is None or unit_price < 0:
            raise ValueError("unit_price must be zero or greater")
        is_courtesy = bool(row.get("is_courtesy", False))
        subtotal = Decimal("0.00") if is_courtesy else _line_subtotal(int(quantity), unit_price)
        db.session.add(
            LaundryServiceExtra(
                laundry_service_id=service.id,
                extra_id=extra_id,
                quantity=int(quantity),
                unit_price=unit_price,
                subtotal=subtotal,
                is_courtesy=is_courtesy,
            )
        )
        seen_extra_ids.add(extra_id)


@laundry_service_v2_bp.route("", methods=["GET"])
@jwt_required()
def get_all():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    client_id = request.args.get("client_id", type=int)
    status = request.args.get("status")

    query = _service_query()
    if client_id:
        query = query.filter(LaundryService.client_id == client_id)
    if status:
        query = query.filter(LaundryService.status == status)

    query = query.order_by(LaundryService.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": schema_many.dump(pagination.items),
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }), 200


@laundry_service_v2_bp.route("/weight-quote", methods=["GET"])
@jwt_required()
def quote_weight_service():
    weight_lb = request.args.get("weight_lb", type=float)
    has_other_services_raw = request.args.get("has_other_services", default="false", type=str)
    has_other_services_normalized = (has_other_services_raw or "").strip().lower()
    if has_other_services_normalized in ("true", "1", "yes"):
        has_other_services = True
    elif has_other_services_normalized in ("false", "0", "no", ""):
        has_other_services = False
    else:
        has_other_services = None

    if weight_lb is None:
        return jsonify({"error": "weight_lb is required"}), 400
    if has_other_services is None:
        return jsonify({"error": "has_other_services must be boolean"}), 400

    try:
        result = calculate_weight_service_quote(
            weight_lb=weight_lb,
            has_other_services=has_other_services,
            pricing_config=_load_weight_pricing_config(),
        )
    except (ArithmeticError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result), 200


@laundry_service_v2_bp.route("/delivery-quote", methods=["GET"])
@jwt_required()
def quote_delivery_service():
    fulfillment_type = request.args.get("fulfillment_type", type=str)
    distance_km = request.args.get("distance_km", type=float)
    manual_delivery_fee = request.args.get("manual_delivery_fee", type=float)

    if not fulfillment_type:
        return jsonify({"error": "fulfillment_type is required"}), 400

    normalized_fulfillment_type = fulfillment_type.strip().upper()
    allowed_fulfillment_types = {
        LaundryService.FULFILLMENT_TYPE_WALK_IN,
        LaundryService.FULFILLMENT_TYPE_DELIVERY,
        LaundryService.FULFILLMENT_TYPE_PICKUP_DELIVERY,
    }
    if normalized_fulfillment_type not in allowed_fulfillment_types:
        return jsonify(
            {
                "error": "fulfillment_type must be one of WALK_IN, DELIVERY, PICKUP_DELIVERY"
            }
        ), 400

    if distance_km is None:
        return jsonify({"error": "distance_km is required"}), 400
    if distance_km < 0:
        return jsonify({"error": "distance_km cannot be negative"}), 400

    if manual_delivery_fee is not None and manual_delivery_fee < 0:
        return jsonify({"error": "manual_delivery_fee cannot be negative"}), 400

    if normalized_fulfillment_type == LaundryService.FULFILLMENT_TYPE_WALK_IN:
        return jsonify(
            {
                "error": (
                    "Cannot charge delivery when fulfillment_type is WALK_IN. "
                    "Change fulfillment_type to DELIVERY or PICKUP_DELIVERY."
                )
            }
        ), 400

    try:
        delivery_price_per_km = _load_delivery_price_per_km()
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    distance_decimal = _as_money(distance_km)
    if normalized_fulfillment_type == LaundryService.FULFILLMENT_TYPE_DELIVERY:
        suggested_delivery_fee = _as_money(
            (distance_decimal * delivery_price_per_km) / Decimal("2")
        )
    else:
        suggested_delivery_fee = _as_money(distance_decimal * delivery_price_per_km)

    manual_delivery_fee_money = (
        _as_money(manual_delivery_fee) if manual_delivery_fee is not None else None
    )
    final_delivery_fee = (
        manual_delivery_fee_money
        if manual_delivery_fee_money is not None
        else suggested_delivery_fee
    )

    return jsonify(
        {
            "fulfillment_type": normalized_fulfillment_type,
            "distance_km": f"{distance_decimal:.2f}",
            "delivery_price_per_km": f"{delivery_price_per_km:.2f}",
            "suggested_delivery_fee": f"{suggested_delivery_fee:.2f}",
            "manual_delivery_fee": (
                f"{manual_delivery_fee_money:.2f}" if manual_delivery_fee_money is not None else None
            ),
            "final_delivery_fee": f"{final_delivery_fee:.2f}",
            "is_manual_override": manual_delivery_fee_money is not None,
        }
    ), 200


@laundry_service_v2_bp.route("/<int:service_id>", methods=["GET"])
@jwt_required()
def get_one(service_id):
    service = _service_query().filter(LaundryService.id == service_id).first_or_404()
    return jsonify(schema.dump(service)), 200


@laundry_service_v2_bp.route("/<int:service_id>/summary", methods=["GET"])
@jwt_required()
def get_summary(service_id):
    service = _service_query().filter(LaundryService.id == service_id).first_or_404()
    return jsonify(_build_summary_response(service)), 200


@laundry_service_v2_bp.route("/<int:service_id>/header", methods=["PATCH"])
@jwt_required()
def patch_header(service_id):
    service = _service_query().filter(LaundryService.id == service_id).first_or_404()
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    current_user_id = get_jwt_identity()

    service_label = json_data.get("service_label", service.service_label)
    fulfillment_type = json_data.get("fulfillment_type", service.fulfillment_type)
    distance_km = json_data.get("distance_km")
    manual_delivery_fee = json_data.get("manual_delivery_fee")

    if "service_label" in json_data:
        normalized_service_label = str(service_label).strip().upper()
        if normalized_service_label not in {"NORMAL", "EXPRESS"}:
            return jsonify({"error": "service_label must be NORMAL or EXPRESS"}), 400
        service.service_label = normalized_service_label

    if "fulfillment_type" in json_data:
        normalized_fulfillment_type = str(fulfillment_type).strip().upper()
        if normalized_fulfillment_type not in {
            LaundryService.FULFILLMENT_TYPE_WALK_IN,
            LaundryService.FULFILLMENT_TYPE_DELIVERY,
            LaundryService.FULFILLMENT_TYPE_PICKUP_DELIVERY,
        }:
            return jsonify(
                {"error": "fulfillment_type must be one of WALK_IN, DELIVERY, PICKUP_DELIVERY"}
            ), 400
        service.fulfillment_type = normalized_fulfillment_type

    try:
        _sync_service_type_order_item(service.id, service.service_label)
        _sync_delivery_order_item(
            service.id,
            service.fulfillment_type,
            distance_km=distance_km,
            manual_delivery_fee=manual_delivery_fee,
        )
    except (ArithmeticError, ValueError) as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400

    db.session.commit()
    db.session.add(
        LaundryActivityLog(
            laundry_service_id=service.id,
            user_id=current_user_id,
            action="ACTUALIZACION",
            new_status=map_status_to_log_enum(service.status),
            description="Actualizacion de cabecera operativa V2.",
        )
    )
    db.session.commit()
    service = _service_query().filter(LaundryService.id == service.id).first_or_404()
    return jsonify(_build_summary_response(service)), 200


@laundry_service_v2_bp.route("/<int:service_id>/commercial-detail", methods=["PATCH"])
@jwt_required()
def patch_commercial_detail(service_id):
    service = _service_query().filter(LaundryService.id == service_id).first_or_404()
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    current_user_id = get_jwt_identity()

    try:
        _replace_manual_order_items(service, json_data)
        _replace_extras(service, json_data.get("extras"))
    except (ArithmeticError, ValueError) as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400

    db.session.commit()
    db.session.add(
        LaundryActivityLog(
            laundry_service_id=service.id,
            user_id=current_user_id,
            action="ACTUALIZACION",
            new_status=map_status_to_log_enum(service.status),
            description="Actualizacion de detalle comercial V2.",
        )
    )
    db.session.commit()
    service = _service_query().filter(LaundryService.id == service.id).first_or_404()
    return jsonify(_build_summary_response(service)), 200


@laundry_service_v2_bp.route("", methods=["POST"])
@jwt_required()
def create():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        data = upsert_schema.load(json_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    _, _, validation_error = _validate_client_and_address(data["client_id"], data["client_address_id"])
    if validation_error:
        payload, code = validation_error
        return jsonify(payload), code

    current_user_id = get_jwt_identity()
    service = LaundryService(
        client_id=data["client_id"],
        client_address_id=data["client_address_id"],
        scheduled_pickup_at=data["scheduled_pickup_at"],
        service_label=data["service_label"],
        fulfillment_type=data.get("fulfillment_type", "WALK_IN"),
        status=data["status"],
        transaction_id=data.get("transaction_id"),
        notes=data.get("notes"),
        created_by_user_id=current_user_id,
    )
    if service.status == "PENDING":
        service.pending_order = _next_pending_order()
    else:
        _sync_pending_order_for_status(service)

    db.session.add(service)
    db.session.flush()

    try:
        delivery_order_item = _build_default_delivery_order_item(service.id)
        service_type_order_item = _build_default_service_type_order_item(
            service.id,
            service.service_label,
        )
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400
    db.session.add(delivery_order_item)
    db.session.add(service_type_order_item)
    db.session.commit()

    log = LaundryActivityLog(
        laundry_service_id=service.id,
        user_id=current_user_id,
        action="CREACION",
        new_status=map_status_to_log_enum(service.status),
        description="Creacion del servicio de lavanderia V2.",
    )
    db.session.add(log)
    db.session.commit()

    socketio = _get_socketio()
    if socketio:
        _emit_queue_for_status_and_all(socketio, statuses=[service.status])

    service = _service_query().filter(LaundryService.id == service.id).first_or_404()
    return jsonify(schema.dump(service)), 201


@laundry_service_v2_bp.route("/<int:service_id>", methods=["PUT"])
@jwt_required()
def update(service_id):
    service = _service_query().filter(LaundryService.id == service_id).first_or_404()
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        data = upsert_schema.load(json_data, partial=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    current_user_id = get_jwt_identity()
    old_status = service.status

    next_client_id = data.get("client_id", service.client_id)
    next_address_id = data.get("client_address_id", service.client_address_id)
    _, _, validation_error = _validate_client_and_address(next_client_id, next_address_id)
    if validation_error:
        payload, code = validation_error
        return jsonify(payload), code

    if "client_id" in data:
        service.client_id = data["client_id"]
    if "client_address_id" in data:
        service.client_address_id = data["client_address_id"]
    if "scheduled_pickup_at" in data:
        service.scheduled_pickup_at = data["scheduled_pickup_at"]
    if "service_label" in data:
        service.service_label = data["service_label"]
    if "fulfillment_type" in data:
        service.fulfillment_type = data["fulfillment_type"]
    if "status" in data:
        service.status = data["status"]
    if "transaction_id" in data:
        service.transaction_id = data["transaction_id"]
    if "notes" in data:
        service.notes = data["notes"]

    if old_status != "PENDING" and service.status == "PENDING":
        service.pending_order = _next_pending_order()
    else:
        _sync_pending_order_for_status(service)

    nested_error = _apply_nested_rows(service, data)
    if nested_error:
        payload, code = nested_error
        return jsonify(payload), code

    db.session.commit()

    if old_status != service.status:
        log = LaundryActivityLog(
            laundry_service_id=service.id,
            user_id=current_user_id,
            action="ACTUALIZACION",
            previous_status=map_status_to_log_enum(old_status),
            new_status=map_status_to_log_enum(service.status),
            description="Actualizacion del servicio de lavanderia V2.",
        )
        db.session.add(log)
        db.session.commit()

    socketio = _get_socketio()
    if socketio:
        _emit_queue_for_status_and_all(socketio, statuses=[old_status, service.status])

    service = _service_query().filter(LaundryService.id == service.id).first_or_404()
    return jsonify(schema.dump(service)), 200


@laundry_service_v2_bp.route("/<int:service_id>", methods=["DELETE"])
@jwt_required()
def delete(service_id):
    service = LaundryService.query.get_or_404(service_id)
    old_status = service.status
    db.session.delete(service)
    db.session.commit()

    socketio = _get_socketio()
    if socketio:
        _emit_queue_for_status_and_all(socketio, statuses=[old_status])

    return jsonify({"message": f"LaundryService {service_id} deleted"}), 200
