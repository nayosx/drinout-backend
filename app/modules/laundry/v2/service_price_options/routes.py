from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from db import db
from models.catalog_service import CatalogService
from models.service_price_option import ServicePriceOption
from schemas.service_price_option_schema import ServicePriceOptionSchema


service_price_option_v2_bp = Blueprint(
    "service_price_option_v2_bp",
    __name__,
    url_prefix="/v2/service-price-options",
)

schema = ServicePriceOptionSchema()
schema_many = ServicePriceOptionSchema(many=True)


@service_price_option_v2_bp.route("", methods=["GET"])
@jwt_required()
def get_all():
    query = ServicePriceOption.query
    service_id = request.args.get("service_id", type=int)
    is_active = request.args.get("is_active")
    if service_id:
        query = query.filter(ServicePriceOption.service_id == service_id)
    if is_active is not None:
        query = query.filter(ServicePriceOption.is_active == (is_active.lower() == "true"))
    items = query.order_by(ServicePriceOption.service_id.asc(), ServicePriceOption.sort_order.is_(None), ServicePriceOption.sort_order.asc(), ServicePriceOption.id.asc()).all()
    return jsonify(schema_many.dump(items)), 200


@service_price_option_v2_bp.route("/<int:item_id>", methods=["GET"])
@jwt_required()
def get_one(item_id):
    item = ServicePriceOption.query.get_or_404(item_id)
    return jsonify(schema.dump(item)), 200


@service_price_option_v2_bp.route("", methods=["POST"])
@jwt_required()
def create():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    service = CatalogService.query.get(data["service_id"])
    if not service:
        return jsonify({"error": "Service not found"}), 404

    item = ServicePriceOption(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Service price option created", "service_price_option": schema.dump(item)}), 201


@service_price_option_v2_bp.route("/<int:item_id>", methods=["PATCH"])
@jwt_required()
def update(item_id):
    item = ServicePriceOption.query.get_or_404(item_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = schema.load(json_data, partial=True)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    if "service_id" in data:
        service = CatalogService.query.get(data["service_id"])
        if not service:
            return jsonify({"error": "Service not found"}), 404

    for key, value in data.items():
        setattr(item, key, value)
    db.session.commit()
    return jsonify({"message": "Service price option updated", "service_price_option": schema.dump(item)}), 200
