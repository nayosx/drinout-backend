from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from db import db
from models.delivery_zone import DeliveryZone, DeliveryZonePrice
from schemas.delivery_zone_schema import DeliveryZonePriceSchema, DeliveryZoneSchema


delivery_zone_v2_bp = Blueprint(
    "delivery_zone_v2_bp",
    __name__,
    url_prefix="/v2/delivery-zones",
)

schema = DeliveryZoneSchema()
schema_many = DeliveryZoneSchema(many=True)
price_schema = DeliveryZonePriceSchema()


def _append_current_price(zone, current_fee):
    if current_fee is None:
        return
    price = DeliveryZonePrice(
        delivery_zone=zone,
        fee_amount=current_fee,
        is_active=True,
    )
    db.session.add(price)


@delivery_zone_v2_bp.route("", methods=["GET"])
@jwt_required()
def get_all():
    query = DeliveryZone.query
    is_active = request.args.get("is_active")
    if is_active is not None:
        query = query.filter(DeliveryZone.is_active == (is_active.lower() == "true"))
    items = query.order_by(DeliveryZone.name.asc()).all()
    return jsonify(schema_many.dump(items)), 200


@delivery_zone_v2_bp.route("/<int:item_id>", methods=["GET"])
@jwt_required()
def get_one(item_id):
    item = DeliveryZone.query.get_or_404(item_id)
    return jsonify(schema.dump(item)), 200


@delivery_zone_v2_bp.route("", methods=["POST"])
@jwt_required()
def create():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    current_fee = data.pop("current_fee", None)
    item = DeliveryZone(**data)
    db.session.add(item)
    db.session.flush()
    _append_current_price(item, current_fee)
    db.session.commit()
    return jsonify({"message": "Delivery zone created", "delivery_zone": schema.dump(item)}), 201


@delivery_zone_v2_bp.route("/<int:item_id>", methods=["PATCH"])
@jwt_required()
def update(item_id):
    item = DeliveryZone.query.get_or_404(item_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = schema.load(json_data, partial=True)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    current_fee = data.pop("current_fee", None)
    for key, value in data.items():
        setattr(item, key, value)
    _append_current_price(item, current_fee)
    db.session.commit()
    return jsonify({"message": "Delivery zone updated", "delivery_zone": schema.dump(item)}), 200


@delivery_zone_v2_bp.route("/<int:zone_id>/prices", methods=["POST"])
@jwt_required()
def create_price(zone_id):
    zone = DeliveryZone.query.get_or_404(zone_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    json_data["delivery_zone_id"] = zone.id
    try:
        data = price_schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    item = DeliveryZonePrice(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Delivery zone price created", "delivery_zone_price": price_schema.dump(item)}), 201
