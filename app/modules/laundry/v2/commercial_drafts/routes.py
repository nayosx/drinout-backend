import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.modules.laundry.v2.orders.routes import (
    _active_zone_price,
    _build_extra_items,
    _build_order_items,
    _calculate_payment_surcharge,
    _create_status_history,
    _order_query,
    _resolve_profile,
    _validate_client,
    _validate_payment_type,
    _validate_user,
    money,
)
from app.modules.laundry.v2.services.routes import _build_extra_models, _build_item_models
from app.services.weight_pricing import WeightPricingEngine
from db import db
from models.catalog_service import CatalogService
from models.extra_catalog import ExtraCatalog
from models.laundry_service_commercial_draft import LaundryServiceCommercialDraft
from models.laundry_service import LaundryService
from models.order import Order
from models.service_extra_type import ServiceExtraType
from models.service_price_option import ServicePriceOption
from models.weight_pricing_profile import WeightPricingProfile
from schemas.laundry_service_commercial_draft_schema import (
    LaundryServiceCommercialDraftCreateSchema,
    LaundryServiceCommercialDraftPatchSchema,
    LaundryServiceCommercialDraftSchema,
)
from schemas.order_schema import OrderSchema


commercial_draft_v2_bp = Blueprint(
    "commercial_draft_v2_bp",
    __name__,
    url_prefix="/v2/laundry-service-commercial-drafts",
)

schema = LaundryServiceCommercialDraftSchema()
schema_many = LaundryServiceCommercialDraftSchema(many=True)
create_schema = LaundryServiceCommercialDraftCreateSchema()
patch_schema = LaundryServiceCommercialDraftPatchSchema()
order_schema = OrderSchema()


def _to_decimal(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        amount = value
    else:
        amount = Decimal(str(value))
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _to_datetime(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _payload_root(payload):
    if isinstance(payload, dict) and isinstance(payload.get("ui_model"), dict):
        return payload["ui_model"]
    return payload if isinstance(payload, dict) else {}


def _payload_service_root(payload):
    if isinstance(payload, dict) and isinstance(payload.get("laundry_service_payload"), dict):
        return payload["laundry_service_payload"]
    return _payload_root(payload)


def _resolve_pricing_profile(profile_id):
    if profile_id:
        return WeightPricingProfile.query.get(profile_id)
    return (
        WeightPricingProfile.query.filter_by(is_active=True)
        .order_by(WeightPricingProfile.id.asc())
        .first()
    )


def _commercial_entry_has_positive_price(entry):
    if not isinstance(entry, dict):
        return False

    manual_price = entry.get("manual_price")
    if manual_price is not None and _to_decimal(manual_price) and _to_decimal(manual_price) > Decimal("0.00"):
        return True

    selected_price_option_id = entry.get("selected_price_option_id")
    service_id = entry.get("service_id")
    if selected_price_option_id is not None and service_id is not None:
        option = ServicePriceOption.query.get(selected_price_option_id)
        if option and option.service_id == service_id and _to_decimal(option.suggested_price) > Decimal("0.00"):
            return True

    if service_id is not None:
        service = CatalogService.query.get(service_id)
        if service and service.pricing_mode != "WEIGHT":
            return True

    return False


def _draft_has_billable_companion_service(root):
    pending_rows = root.get("commercial_capture_pending")
    if not isinstance(pending_rows, list):
        return False
    return any(_commercial_entry_has_positive_price(row) for row in pending_rows)


def _refresh_weight_pricing_preview(payload):
    root = _payload_root(payload)
    weight_lb = root.get("weight_lb")
    if weight_lb in (None, ""):
        return payload

    profile = _resolve_pricing_profile(root.get("pricing_profile_id"))
    if not profile:
        return payload

    allow_small_weight_by_lb = _draft_has_billable_companion_service(root)
    quote = WeightPricingEngine(profile).quote(
        weight_lb,
        allow_small_weight_by_lb=allow_small_weight_by_lb,
    )

    preview = root.get("weight_pricing_preview")
    if not isinstance(preview, dict):
        preview = {}

    preview.update(
        {
            "profile_id": quote["profile_id"],
            "profile_name": quote["profile_name"],
            "weight_lb": quote["weight_lb"],
            "strategy_applied": quote["strategy_selected"],
            "recommended_price": quote["recommended_price"],
            "final_price": quote["recommended_price"],
            "min_valid_price": quote["lowest_valid_price"],
            "max_valid_price": quote["highest_valid_price"],
            "allow_manual_override": quote["allow_manual_override"],
            "business_reason": quote["decision_reason"],
            "evaluated_options": quote["options_evaluated"],
        }
    )
    root["weight_pricing_preview"] = preview
    root["quoted_service_amount"] = quote["recommended_price"]
    return payload


def _get_laundry_service_or_404(laundry_service_id):
    item = LaundryService.query.get(laundry_service_id)
    if not item:
        return None, ({"error": "LaundryService not found"}, 404)
    return item, None


def _apply_payload_snapshot(item, payload):
    payload = _refresh_weight_pricing_preview(payload)
    root = _payload_root(payload)
    preview = root.get("weight_pricing_preview") if isinstance(root.get("weight_pricing_preview"), dict) else {}

    item.client_id = root.get("client_id")
    item.client_address_id = root.get("client_address_id")
    item.transaction_id = root.get("transaction_id")
    item.payment_type_id = root.get("payment_type_id")
    item.pricing_profile_id = root.get("pricing_profile_id")
    item.status = root.get("status")
    item.service_label = root.get("service_label")
    item.scheduled_pickup_at = _to_datetime(root.get("scheduled_pickup_at"))
    item.weight_lb = _to_decimal(root.get("weight_lb"))
    item.distance_km = _to_decimal(root.get("distance_km"))
    item.delivery_price_per_km = _to_decimal(root.get("delivery_price_per_km"))
    item.delivery_fee_suggested = _to_decimal(root.get("delivery_fee_suggested"))
    item.delivery_fee_final = _to_decimal(root.get("delivery_fee_final"))
    item.delivery_fee_override_reason = root.get("delivery_fee_override_reason")
    item.global_discount_amount = _to_decimal(root.get("global_discount_amount"))
    item.global_discount_reason = root.get("global_discount_reason")
    item.quoted_service_amount = _to_decimal(root.get("quoted_service_amount"))
    if item.quoted_service_amount is None:
        item.quoted_service_amount = _to_decimal(preview.get("final_price"))
    item.notes = root.get("notes")
    item.payload_json = json.dumps(payload, ensure_ascii=True)


def _sync_laundry_service_from_payload(laundry_service, payload):
    root = _payload_root(payload)
    if "client_id" in root:
        laundry_service.client_id = root.get("client_id")
    if "client_address_id" in root:
        laundry_service.client_address_id = root.get("client_address_id")
    if "scheduled_pickup_at" in root:
        laundry_service.scheduled_pickup_at = _to_datetime(root.get("scheduled_pickup_at"))
    if "status" in root:
        laundry_service.status = root.get("status")
    if "service_label" in root:
        laundry_service.service_label = root.get("service_label")
    if "transaction_id" in root:
        laundry_service.transaction_id = root.get("transaction_id")
    if "weight_lb" in root:
        laundry_service.weight_lb = _to_decimal(root.get("weight_lb"))
    if "notes" in root:
        laundry_service.notes = root.get("notes")


def _normalized_payload(item):
    payload = json.loads(item.payload_json)
    return _refresh_weight_pricing_preview(payload)


def _sync_laundry_service_rows_from_payload(laundry_service, payload):
    service_root = _payload_service_root(payload)
    if not isinstance(service_root, dict):
        return None

    if "items" in service_root:
        item_models, item_error = _build_item_models(service_root.get("items") or [])
        if item_error:
            return item_error
        laundry_service.items = item_models

    if "extras" in service_root:
        extra_models, extra_error = _build_extra_models(service_root.get("extras") or [])
        if extra_error:
            return extra_error
        laundry_service.extras = extra_models

    return None


def _normalize_row_decimal(value):
    if value in (None, ""):
        return None
    return str(_to_decimal(value))


def _build_order_item_rows_from_draft(root):
    items = []
    pending_rows = root.get("commercial_capture_pending")
    if isinstance(pending_rows, list):
        for row in pending_rows:
            if not isinstance(row, dict) or row.get("service_id") is None:
                continue
            item_data = {
                "service_id": row["service_id"],
                "suggested_price_option_id": row.get("selected_price_option_id"),
                "quantity": _normalize_row_decimal(row.get("quantity") or 1),
                "discount_amount": _normalize_row_decimal(row.get("discount_amount") or 0) or "0.00",
                "notes": row.get("notes"),
                "manual_price_override_reason": row.get("manual_price_override_reason"),
            }
            if row.get("manual_price") is not None:
                item_data["final_unit_price"] = _normalize_row_decimal(row.get("manual_price"))
                item_data["manual_price_override_reason"] = (
                    row.get("manual_price_override_reason")
                    or "Precio manual definido en draft comercial"
                )
            items.append(item_data)

    preview = root.get("weight_pricing_preview") if isinstance(root.get("weight_pricing_preview"), dict) else {}
    weight_lb = root.get("weight_lb")
    weight_service_id = preview.get("service_id")
    weight_service = None
    if weight_service_id:
        weight_service = CatalogService.query.get(weight_service_id)
    if not weight_service:
        weight_service = (
            CatalogService.query.filter_by(pricing_mode="WEIGHT", is_active=True)
            .order_by(CatalogService.id.asc())
            .first()
        )

    final_price = preview.get("final_price") or root.get("quoted_service_amount")
    if weight_service and weight_lb not in (None, "") and final_price not in (None, ""):
        recommended_price = preview.get("recommended_price")
        weight_item = {
            "service_id": weight_service.id,
            "quantity": "1.00",
            "weight_lb": _normalize_row_decimal(weight_lb),
            "final_unit_price": _normalize_row_decimal(final_price),
            "discount_amount": "0.00",
            "notes": "Lavado por peso desde draft comercial",
        }
        if recommended_price not in (None, "") and _to_decimal(recommended_price) != _to_decimal(final_price):
            weight_item["manual_price_override_reason"] = (
                preview.get("business_reason")
                or "Override manual del precio por peso desde draft comercial"
            )
        items.insert(0, weight_item)

    return items


def _normalize_code(value):
    if value is None:
        return None
    return "".join(char for char in str(value).upper() if char.isalnum())


def _resolve_order_extra_catalog_id(service_extra_type_id):
    extra_type = ServiceExtraType.query.get(service_extra_type_id)
    if not extra_type:
        return None

    exact_code_map = {
        "SCENTBEADS": "PERLITASOLOR",
        "SOAK": "REMOJO",
        "VINEGAR": "VINAGRE",
        "VANISH": "VANISH",
    }

    normalized_type_code = _normalize_code(extra_type.code)
    normalized_type_name = _normalize_code(extra_type.name)
    candidate_codes = [normalized_type_code, exact_code_map.get(normalized_type_code)]
    candidate_names = [normalized_type_name]

    for extra in ExtraCatalog.query.filter_by(is_active=True).all():
        normalized_extra_code = _normalize_code(extra.code)
        normalized_extra_name = _normalize_code(extra.name)
        if normalized_extra_code in candidate_codes or normalized_extra_name in candidate_names:
            return extra.id

    return None


def _build_order_extra_rows_from_draft(root):
    extras = []
    draft_extras = root.get("extras")
    if not isinstance(draft_extras, list):
        return extras

    for row in draft_extras:
        if not isinstance(row, dict) or row.get("service_extra_type_id") is None:
            continue
        extra_catalog_id = _resolve_order_extra_catalog_id(row["service_extra_type_id"])
        if extra_catalog_id is None:
            extra_type = ServiceExtraType.query.get(row["service_extra_type_id"])
            extra_name = extra_type.name if extra_type else row["service_extra_type_id"]
            raise ValueError(
                f"No existe mapeo de extra comercial para service_extra_type_id={row['service_extra_type_id']} ({extra_name})"
            )

        extra_data = {
            "extra_id": extra_catalog_id,
            "quantity": _normalize_row_decimal(row.get("quantity") or 1),
            "discount_amount": _normalize_row_decimal(row.get("discount_amount") or 0) or "0.00",
            "notes": row.get("notes"),
        }
        if row.get("unit_price") is not None:
            extra_data["final_unit_price"] = _normalize_row_decimal(row.get("unit_price"))
        extras.append(extra_data)

    return extras


def _draft_order_payload(payload, root, item):
    order_payload = payload.get("order_payload") if isinstance(payload, dict) else None
    if isinstance(order_payload, dict):
        base = dict(order_payload)
    else:
        base = {}

    base.setdefault("client_id", root.get("client_id"))
    base.setdefault("client_address_id", root.get("client_address_id"))
    base.setdefault("pricing_profile_id", root.get("pricing_profile_id"))
    base.setdefault("payment_type_id", root.get("payment_type_id"))
    base.setdefault("delivery_zone_id", root.get("delivery_zone_id"))
    base.setdefault("delivery_fee_final", _normalize_row_decimal(root.get("delivery_fee_final") or 0) or "0.00")
    base.setdefault("delivery_fee_override_reason", root.get("delivery_fee_override_reason"))
    base.setdefault("status", "CONFIRMED")
    base.setdefault(
        "global_discount_amount",
        _normalize_row_decimal(root.get("global_discount_amount") or 0) or "0.00",
    )
    base.setdefault("global_discount_reason", root.get("global_discount_reason"))
    base.setdefault("notes", root.get("notes"))
    base.setdefault("charged_by_user_id", item.charged_by_user_id)
    base["items"] = _build_order_item_rows_from_draft(root)
    base["extras"] = _build_order_extra_rows_from_draft(root)
    return base


def _build_order_from_draft(item, payload):
    root = _payload_root(payload)
    order_data = _draft_order_payload(payload, root, item)

    if not order_data.get("client_id"):
        return None, ({"error": "client_id is required to confirm the commercial draft"}, 400)
    if not order_data.get("payment_type_id"):
        return None, ({"error": "payment_type_id is required to confirm the commercial draft"}, 400)
    if not order_data.get("items"):
        return None, ({"error": "At least one commercial item is required to confirm the draft"}, 400)

    _, _, validation_error = _validate_client(order_data["client_id"], order_data.get("client_address_id"))
    if validation_error:
        payload_error, status_code = validation_error
        return None, (payload_error, status_code)

    current_user_id = get_jwt_identity()
    charged_by_user_id = order_data.get("charged_by_user_id") or current_user_id
    user_error = _validate_user(charged_by_user_id, "charged_by")
    if user_error:
        payload_error, status_code = user_error
        return None, (payload_error, status_code)

    pricing_profile, profile_error = _resolve_profile(order_data.get("pricing_profile_id"))
    if profile_error:
        payload_error, status_code = profile_error
        return None, (payload_error, status_code)

    payment_type, payment_type_error = _validate_payment_type(order_data["payment_type_id"])
    if payment_type_error:
        payload_error, status_code = payment_type_error
        return None, (payload_error, status_code)

    delivery_zone = None
    delivery_zone_price = None
    delivery_fee_suggested = Decimal("0.00")
    delivery_fee_final = Decimal("0.00")
    if order_data.get("delivery_zone_id") is not None:
        delivery_zone_price = _active_zone_price(order_data["delivery_zone_id"])
        if not delivery_zone_price:
            return None, ({"error": "Active delivery price not found for zone"}, 400)
        delivery_zone = delivery_zone_price.delivery_zone
        delivery_fee_suggested = money(delivery_zone_price.fee_amount)
        delivery_fee_final = money(order_data.get("delivery_fee_final", delivery_fee_suggested))
    elif order_data.get("delivery_fee_final") is not None:
        delivery_fee_final = money(order_data["delivery_fee_final"])

    order = Order(
        client_id=order_data["client_id"],
        client_address_id=order_data.get("client_address_id"),
        pricing_profile_id=pricing_profile.id if pricing_profile else None,
        payment_type_id=payment_type.id,
        delivery_zone_id=delivery_zone.id if delivery_zone else None,
        delivery_zone_price_id=delivery_zone_price.id if delivery_zone_price else None,
        status=order_data.get("status") or "CONFIRMED",
        delivery_fee_suggested=delivery_fee_suggested,
        delivery_fee_final=delivery_fee_final,
        delivery_fee_override_by_user_id=(
            current_user_id if delivery_fee_final != delivery_fee_suggested else None
        ),
        delivery_fee_override_reason=(
            order_data.get("delivery_fee_override_reason")
            if delivery_fee_final != delivery_fee_suggested
            else None
        ),
        global_discount_amount=money(order_data.get("global_discount_amount", 0)),
        global_discount_reason=order_data.get("global_discount_reason"),
        payment_type_name_snapshot=payment_type.name,
        payment_surcharge_type_snapshot=payment_type.surcharge_type,
        payment_surcharge_value_snapshot=payment_type.surcharge_value,
        notes=order_data.get("notes"),
        charged_by_user_id=charged_by_user_id,
        created_by_user_id=current_user_id,
        updated_by_user_id=current_user_id,
    )
    db.session.add(order)
    db.session.flush()

    try:
        item_models, snapshot_models, service_subtotal = _build_order_items(
            order,
            order_data["items"],
            pricing_profile,
            current_user_id,
        )
    except ValueError as exc:
        db.session.rollback()
        return None, ({"error": str(exc)}, 400)

    if item_models is None:
        db.session.rollback()
        payload_error, status_code = service_subtotal
        return None, (payload_error, status_code)

    try:
        extra_models, extras_subtotal, extras_error = _build_extra_items(order_data.get("extras", []))
    except ValueError as exc:
        db.session.rollback()
        return None, ({"error": str(exc)}, 400)

    if extras_error:
        db.session.rollback()
        payload_error, status_code = extras_error
        return None, (payload_error, status_code)

    order.items = item_models
    order.extra_items = extra_models
    db.session.flush()

    for item_model, snapshot in snapshot_models:
        snapshot.order_item_id = item_model.id
        item_model.weight_pricing_snapshot = snapshot
        db.session.add(snapshot)

    order.service_subtotal = money(service_subtotal)
    order.extras_subtotal = money(extras_subtotal)
    order.subtotal_before_payment_surcharge = money(
        order.service_subtotal
        + order.extras_subtotal
        + order.delivery_fee_final
        - money(order.global_discount_amount)
    )
    if order.subtotal_before_payment_surcharge < 0:
        db.session.rollback()
        return None, ({"error": "global_discount_amount cannot exceed order total"}, 400)
    order.payment_surcharge_amount = _calculate_payment_surcharge(
        order.subtotal_before_payment_surcharge,
        payment_type,
    )
    order.total_amount = money(order.subtotal_before_payment_surcharge + order.payment_surcharge_amount)
    _create_status_history(order, None, order.status, current_user_id, "Commercial draft confirmation")
    return order, None


def _serialize(item):
    data = schema.dump(item)
    payload = _normalized_payload(item)
    root = _payload_root(payload)
    data["payload"] = payload
    if root.get("quoted_service_amount") is not None:
        data["quoted_service_amount"] = str(_to_decimal(root.get("quoted_service_amount")))
    return data


@commercial_draft_v2_bp.route("", methods=["GET"])
@jwt_required()
def get_all():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    client_id = request.args.get("client_id", type=int)
    laundry_service_id = request.args.get("laundry_service_id", type=int)
    is_confirmed = request.args.get("is_confirmed")

    query = LaundryServiceCommercialDraft.query
    if client_id:
        query = query.filter(LaundryServiceCommercialDraft.client_id == client_id)
    if laundry_service_id:
        query = query.filter(LaundryServiceCommercialDraft.laundry_service_id == laundry_service_id)
    if is_confirmed is not None:
        query = query.filter(LaundryServiceCommercialDraft.is_confirmed == (is_confirmed.lower() == "true"))

    pagination = query.order_by(LaundryServiceCommercialDraft.id.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )
    return jsonify(
        {
            "items": [_serialize(item) for item in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages,
        }
    ), 200


@commercial_draft_v2_bp.route("/<int:item_id>", methods=["GET"])
@jwt_required()
def get_one(item_id):
    item = LaundryServiceCommercialDraft.query.get_or_404(item_id)
    return jsonify(_serialize(item)), 200


@commercial_draft_v2_bp.route("/by-service/<int:laundry_service_id>", methods=["GET"])
@jwt_required()
def get_one_by_service(laundry_service_id):
    item = LaundryServiceCommercialDraft.query.filter_by(
        laundry_service_id=laundry_service_id
    ).first_or_404()
    return jsonify(_serialize(item)), 200


@commercial_draft_v2_bp.route("", methods=["POST"])
@jwt_required()
def create():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = create_schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    existing = LaundryServiceCommercialDraft.query.filter_by(
        laundry_service_id=data["laundry_service_id"]
    ).first()
    if existing:
        return jsonify({"error": "Commercial draft already exists for this laundry_service_id"}), 400

    laundry_service, laundry_service_error = _get_laundry_service_or_404(data["laundry_service_id"])
    if laundry_service_error:
        payload, status_code = laundry_service_error
        return jsonify(payload), status_code

    current_user_id = get_jwt_identity()
    item = LaundryServiceCommercialDraft(
        laundry_service_id=data["laundry_service_id"],
        is_confirmed=data.get("is_confirmed", False),
        confirmed_at=data.get("confirmed_at"),
        charged_by_user_id=data.get("charged_by_user_id"),
        created_by_user_id=current_user_id,
        updated_by_user_id=current_user_id,
        payload_json="{}",
    )
    _apply_payload_snapshot(item, data["payload"])
    _sync_laundry_service_from_payload(laundry_service, data["payload"])
    row_sync_error = _sync_laundry_service_rows_from_payload(laundry_service, data["payload"])
    if row_sync_error:
        payload, status_code = row_sync_error
        return jsonify(payload), status_code
    db.session.add(item)
    db.session.commit()
    return jsonify(_serialize(item)), 201


@commercial_draft_v2_bp.route("/<int:item_id>", methods=["PATCH"])
@jwt_required()
def update(item_id):
    item = LaundryServiceCommercialDraft.query.get_or_404(item_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = patch_schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    if "laundry_service_id" in data:
        existing = LaundryServiceCommercialDraft.query.filter(
            LaundryServiceCommercialDraft.laundry_service_id == data["laundry_service_id"],
            LaundryServiceCommercialDraft.id != item.id,
        ).first()
        if existing:
            return jsonify({"error": "Commercial draft already exists for this laundry_service_id"}), 400
        laundry_service, laundry_service_error = _get_laundry_service_or_404(data["laundry_service_id"])
        if laundry_service_error:
            payload, status_code = laundry_service_error
            return jsonify(payload), status_code
        item.laundry_service_id = data["laundry_service_id"]
    else:
        laundry_service, laundry_service_error = _get_laundry_service_or_404(item.laundry_service_id)
        if laundry_service_error:
            payload, status_code = laundry_service_error
            return jsonify(payload), status_code
    if "is_confirmed" in data:
        item.is_confirmed = data["is_confirmed"]
    if "confirmed_at" in data:
        item.confirmed_at = data["confirmed_at"]
    if "charged_by_user_id" in data:
        item.charged_by_user_id = data["charged_by_user_id"]
    if "payload" in data:
        _apply_payload_snapshot(item, data["payload"])
        _sync_laundry_service_from_payload(laundry_service, data["payload"])
        row_sync_error = _sync_laundry_service_rows_from_payload(laundry_service, data["payload"])
        if row_sync_error:
            payload, status_code = row_sync_error
            return jsonify(payload), status_code

    item.updated_by_user_id = get_jwt_identity()
    db.session.commit()
    return jsonify(_serialize(item)), 200


@commercial_draft_v2_bp.route("/by-service/<int:laundry_service_id>", methods=["PUT"])
@jwt_required()
def upsert_by_service(laundry_service_id):
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    payload = json_data.get("payload")
    if payload is None:
        return jsonify({"error": "payload is required"}), 400

    item = LaundryServiceCommercialDraft.query.filter_by(
        laundry_service_id=laundry_service_id
    ).first()
    current_user_id = get_jwt_identity()
    laundry_service, laundry_service_error = _get_laundry_service_or_404(laundry_service_id)
    if laundry_service_error:
        payload, status_code = laundry_service_error
        return jsonify(payload), status_code

    if item is None:
        item = LaundryServiceCommercialDraft(
            laundry_service_id=laundry_service_id,
            is_confirmed=bool(json_data.get("is_confirmed", False)),
            confirmed_at=json_data.get("confirmed_at"),
            charged_by_user_id=json_data.get("charged_by_user_id"),
            created_by_user_id=current_user_id,
            updated_by_user_id=current_user_id,
            payload_json="{}",
        )
        _apply_payload_snapshot(item, payload)
        _sync_laundry_service_from_payload(laundry_service, payload)
        row_sync_error = _sync_laundry_service_rows_from_payload(laundry_service, payload)
        if row_sync_error:
            payload_error, status_code = row_sync_error
            return jsonify(payload_error), status_code
        db.session.add(item)
        db.session.commit()
        return jsonify(_serialize(item)), 201

    item.is_confirmed = bool(json_data.get("is_confirmed", item.is_confirmed))
    if "confirmed_at" in json_data:
        item.confirmed_at = json_data.get("confirmed_at")
    if "charged_by_user_id" in json_data:
        item.charged_by_user_id = json_data.get("charged_by_user_id")
    _apply_payload_snapshot(item, payload)
    _sync_laundry_service_from_payload(laundry_service, payload)
    row_sync_error = _sync_laundry_service_rows_from_payload(laundry_service, payload)
    if row_sync_error:
        payload_error, status_code = row_sync_error
        return jsonify(payload_error), status_code
    item.updated_by_user_id = current_user_id
    db.session.commit()
    return jsonify(_serialize(item)), 200


@commercial_draft_v2_bp.route("/by-service/<int:laundry_service_id>/confirm", methods=["POST"])
@jwt_required()
def confirm_by_service(laundry_service_id):
    item = LaundryServiceCommercialDraft.query.filter_by(
        laundry_service_id=laundry_service_id
    ).first_or_404()

    payload = _normalized_payload(item)
    existing_order_payload = payload.get("order_payload")
    if item.is_confirmed and isinstance(existing_order_payload, dict) and existing_order_payload.get("id"):
        existing_order = _order_query().filter(Order.id == existing_order_payload["id"]).first()
        if existing_order:
            return jsonify({"draft": _serialize(item), "order": order_schema.dump(existing_order)}), 200

    laundry_service, laundry_service_error = _get_laundry_service_or_404(laundry_service_id)
    if laundry_service_error:
        payload_error, status_code = laundry_service_error
        return jsonify(payload_error), status_code

    row_sync_error = _sync_laundry_service_rows_from_payload(laundry_service, payload)
    if row_sync_error:
        payload_error, status_code = row_sync_error
        return jsonify(payload_error), status_code

    try:
        order, order_error = _build_order_from_draft(item, payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    if order_error:
        payload_error, status_code = order_error
        return jsonify(payload_error), status_code

    db.session.flush()
    persisted_order = _order_query().filter(Order.id == order.id).first_or_404()
    payload["order_payload"] = order_schema.dump(persisted_order)
    item.is_confirmed = True
    item.confirmed_at = datetime.utcnow()
    item.charged_by_user_id = item.charged_by_user_id or get_jwt_identity()
    item.updated_by_user_id = get_jwt_identity()
    item.payload_json = json.dumps(
        payload,
        ensure_ascii=True,
    )
    db.session.commit()
    refreshed_order = _order_query().filter(Order.id == order.id).first_or_404()
    return jsonify({"draft": _serialize(item), "order": order_schema.dump(refreshed_order)}), 201


@commercial_draft_v2_bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete(item_id):
    item = LaundryServiceCommercialDraft.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": f"Laundry service commercial draft {item_id} deleted"}), 200
