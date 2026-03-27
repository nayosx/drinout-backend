from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from db import db
from models.service_category import ServiceCategory
from schemas.service_category_schema import ServiceCategorySchema


service_category_v2_bp = Blueprint(
    "service_category_v2_bp",
    __name__,
    url_prefix="/v2/service-categories",
)

schema = ServiceCategorySchema()
schema_many = ServiceCategorySchema(many=True)


@service_category_v2_bp.route("", methods=["GET"])
@jwt_required()
def get_all():
    query = ServiceCategory.query
    is_active = request.args.get("is_active")
    if is_active is not None:
        query = query.filter(ServiceCategory.is_active == (is_active.lower() == "true"))
    items = query.order_by(ServiceCategory.sort_order.is_(None), ServiceCategory.sort_order.asc(), ServiceCategory.name.asc()).all()
    return jsonify(schema_many.dump(items)), 200


@service_category_v2_bp.route("/<int:item_id>", methods=["GET"])
@jwt_required()
def get_one(item_id):
    item = ServiceCategory.query.get_or_404(item_id)
    return jsonify(schema.dump(item)), 200


@service_category_v2_bp.route("", methods=["POST"])
@jwt_required()
def create():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    item = ServiceCategory(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Service category created", "service_category": schema.dump(item)}), 201


@service_category_v2_bp.route("/<int:item_id>", methods=["PATCH"])
@jwt_required()
def update(item_id):
    item = ServiceCategory.query.get_or_404(item_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = schema.load(json_data, partial=True)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    for key, value in data.items():
        setattr(item, key, value)
    db.session.commit()
    return jsonify({"message": "Service category updated", "service_category": schema.dump(item)}), 200
