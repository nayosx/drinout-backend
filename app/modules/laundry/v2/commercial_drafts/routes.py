import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from db import db
from models.laundry_service_commercial_draft import LaundryServiceCommercialDraft
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


def _apply_payload_snapshot(item, payload):
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
    item.quoted_service_amount = _to_decimal(preview.get("final_price"))
    item.notes = root.get("notes")
    item.payload_json = json.dumps(payload, ensure_ascii=True)


def _serialize(item):
    data = schema.dump(item)
    data["payload"] = json.loads(item.payload_json)
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

    current_user_id = get_jwt_identity()
    item = LaundryServiceCommercialDraft(
        laundry_service_id=data.get("laundry_service_id"),
        is_confirmed=data.get("is_confirmed", False),
        confirmed_at=data.get("confirmed_at"),
        charged_by_user_id=data.get("charged_by_user_id"),
        created_by_user_id=current_user_id,
        updated_by_user_id=current_user_id,
        payload_json="{}",
    )
    _apply_payload_snapshot(item, data["payload"])
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
        item.laundry_service_id = data["laundry_service_id"]
    if "is_confirmed" in data:
        item.is_confirmed = data["is_confirmed"]
    if "confirmed_at" in data:
        item.confirmed_at = data["confirmed_at"]
    if "charged_by_user_id" in data:
        item.charged_by_user_id = data["charged_by_user_id"]
    if "payload" in data:
        _apply_payload_snapshot(item, data["payload"])

    item.updated_by_user_id = get_jwt_identity()
    db.session.commit()
    return jsonify(_serialize(item)), 200


@commercial_draft_v2_bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete(item_id):
    item = LaundryServiceCommercialDraft.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": f"Laundry service commercial draft {item_id} deleted"}), 200
