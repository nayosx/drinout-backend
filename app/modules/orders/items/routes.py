import json

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from db import db
from models.catalog_service_legacy import CatalogServiceLegacy
from models.order_item import OrderItem
from schemas.order_item_schema import OrderItemSchema


order_item_bp = Blueprint("order_item_bp", __name__, url_prefix="/order_items")

schema = OrderItemSchema()
schema_many = OrderItemSchema(many=True)


def _normalize_snapshot(data):
    if "calculation_snapshot" not in data:
        return data
    snapshot = data["calculation_snapshot"]
    if snapshot is None or isinstance(snapshot, str):
        return data
    data["calculation_snapshot"] = json.dumps(snapshot, ensure_ascii=True)
    return data


def _validate_service_mode_payload(data, current_item=None):
    service_id = data.get("service_id")
    if service_id is None and current_item is not None:
        service_id = current_item.service_id
    if service_id is None:
        return {"error": "service_id is required"}, 400

    service = CatalogServiceLegacy.query.get(service_id)
    if not service:
        return {"error": "Service not found"}, 404

    service_variant_id = data.get("service_variant_id")
    garment_type_id = data.get("garment_type_id")
    if current_item is not None:
        if "service_variant_id" not in data:
            service_variant_id = current_item.service_variant_id
        if "garment_type_id" not in data:
            garment_type_id = current_item.garment_type_id

    if service.pricing_mode == CatalogServiceLegacy.PRICING_MODE_WEIGHT:
        if garment_type_id is None:
            return {"error": "garment_type_id is required for WEIGHT services"}, 400
        if service_variant_id is not None:
            return {"error": "service_variant_id must be null for WEIGHT services"}, 400
        return None

    if service.pricing_mode == CatalogServiceLegacy.PRICING_MODE_DELIVERY:
        if garment_type_id is not None:
            return {"error": "garment_type_id must be null for DELIVERY services"}, 400
        if service_variant_id is not None:
            return {"error": "service_variant_id must be null for DELIVERY services"}, 400
        return None

    if garment_type_id is not None:
        return {"error": "garment_type_id only applies to WEIGHT services"}, 400

    return None


@order_item_bp.route("", methods=["GET"])
@jwt_required()
def get_all():
    query = OrderItem.query
    laundry_service_id = request.args.get("laundry_service_id", type=int)
    service_id = request.args.get("service_id", type=int)
    if laundry_service_id is not None:
        query = query.filter(OrderItem.laundry_service_id == laundry_service_id)
    if service_id is not None:
        query = query.filter(OrderItem.service_id == service_id)
    items = query.order_by(OrderItem.id.desc()).all()
    return jsonify(schema_many.dump(items)), 200


@order_item_bp.route("/<int:item_id>", methods=["GET"])
@jwt_required()
def get_one(item_id):
    item = OrderItem.query.get_or_404(item_id)
    return jsonify(schema.dump(item)), 200


@order_item_bp.route("", methods=["POST"])
@jwt_required()
def create():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    data = _normalize_snapshot(data)
    validation_error = _validate_service_mode_payload(data)
    if validation_error:
        payload, code = validation_error
        return jsonify(payload), code
    item = OrderItem(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Order item created", "item": schema.dump(item)}), 201


@order_item_bp.route("/<int:item_id>", methods=["PUT"])
@jwt_required()
def update(item_id):
    item = OrderItem.query.get_or_404(item_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = schema.load(json_data, partial=True)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    data = _normalize_snapshot(data)
    validation_error = _validate_service_mode_payload(data, current_item=item)
    if validation_error:
        payload, code = validation_error
        return jsonify(payload), code
    for key, value in data.items():
        setattr(item, key, value)
    db.session.commit()
    return jsonify({"message": "Order item updated", "item": schema.dump(item)}), 200


@order_item_bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete(item_id):
    item = OrderItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": f"Order item {item_id} deleted"}), 200
