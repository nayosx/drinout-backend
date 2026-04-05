import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services.weight_pricing import WeightPricingEngine
from db import db
from models.catalog_service import CatalogService
from models.laundry_service_commercial_draft import LaundryServiceCommercialDraft
from models.laundry_service import LaundryService
from models.service_price_option import ServicePriceOption
from models.weight_pricing_profile import WeightPricingProfile
from schemas.laundry_service_commercial_draft_schema import (
    LaundryServiceCommercialDraftCreateSchema,
    LaundryServiceCommercialDraftPatchSchema,
    LaundryServiceCommercialDraftSchema,
)


commercial_draft_v2_bp = Blueprint(
    "commercial_draft_v2_bp",
    __name__,
    url_prefix="/v2/laundry-service-commercial-drafts",
)

schema = LaundryServiceCommercialDraftSchema()
schema_many = LaundryServiceCommercialDraftSchema(many=True)
create_schema = LaundryServiceCommercialDraftCreateSchema()
patch_schema = LaundryServiceCommercialDraftPatchSchema()


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
    item.updated_by_user_id = current_user_id
    db.session.commit()
    return jsonify(_serialize(item)), 200


@commercial_draft_v2_bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete(item_id):
    item = LaundryServiceCommercialDraft.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": f"Laundry service commercial draft {item_id} deleted"}), 200
